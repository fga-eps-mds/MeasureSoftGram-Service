import requests
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response
from django.core.cache import cache
from django.conf import settings

from organizations.mixins import UserScopedMixin
from organizations.models import Organization, Product, Repository
from organizations.serializers import (
    OrganizationSerializer,
    ProductSerializer,
    RepositoriesTSQMIHistorySerializer,
    RepositorySerializer,
    RepositoryTSQMILatestValueSerializer,
)


class OrganizationViewSet(UserScopedMixin, viewsets.ModelViewSet):
    queryset = Organization.objects.all().order_by("id").prefetch_related("products")
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.get_user_organizations().order_by("id").prefetch_related("products")

    def perform_create(self, serializer):
        org = serializer.save(admin=self.request.user)
        org.members.add(self.request.user)


class ProductViewSet(UserScopedMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("-id").select_related("organization").prefetch_related("repositories")
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org = self.get_organization()
        qs = Product.objects.all().order_by("-id").select_related("organization").prefetch_related("repositories")
        return qs.filter(organization=org)

    def perform_create(self, serializer):
        org = self.get_organization()
        serializer.save(organization=org)


class RepositoryViewSetMixin(UserScopedMixin):
    permission_classes = [permissions.IsAuthenticated]


class RepositoryViewSet(
    RepositoryViewSetMixin,
    viewsets.ModelViewSet,
):
    serializer_class = RepositorySerializer
    queryset = Repository.objects.all()

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        product = self.get_product()
        repository = serializer.save(product=product)

        # Trigger background onboarding if not running unit tests
        from django.conf import settings

        if not getattr(settings, "TESTING", False):
            import threading

            from organizations.utils import onboard_repository_async

            thread = threading.Thread(
                target=onboard_repository_async,
                args=(repository, self.request.user),
                daemon=True,
            )
            thread.start()

    def get_queryset(self):
        product = self.get_product()
        qs = Repository.objects.all().order_by("-id").select_related("product", "product__organization")
        return qs.filter(product=product)


class RepositoriesTSQMILatestValueViewSet(
    RepositoryViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Lista o TSQMI mais recente dos repositórios de um produto
    """

    serializer_class = RepositoryTSQMILatestValueSerializer
    queryset = Repository.objects.all()

    def get_queryset(self):
        product = self.get_product()
        qs = product.repositories.all()
        qs = qs.order_by("-id")
        qs = qs.select_related("product", "product__organization").prefetch_related("calculated_tsqmis")
        return qs


class RepositoriesTSQMIHistoryViewSet(
    RepositoryViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = RepositoriesTSQMIHistorySerializer
    queryset = Repository.objects.all()

    def get_queryset(self):
        product = self.get_product()
        qs = product.repositories.all()
        qs = qs.select_related("product", "product__organization").prefetch_related("calculated_tsqmis")
        return qs


class ImportOrganizationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        github_org_name = request.data.get("github_org_name")
        if not github_org_name:
            return Response(
                {"error": "github_org_name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        token = user.github_access_token
        if not token:
            from allauth.socialaccount.models import SocialToken

            st = SocialToken.objects.filter(account__user=user, account__provider="github").first()
            if st:
                token = st.token
                user.github_access_token = token
                user.save()
            else:
                return Response(
                    {"error": "GitHub account not linked."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        is_personal = github_org_name.lower() == user.username.lower()
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/json",
        }

        if is_personal:
            url_fetch = "https://api.github.com/user"
        else:
            url_fetch = f"https://api.github.com/orgs/{github_org_name}"

        r = requests.get(url_fetch, headers=headers)
        if r.status_code != 200:
            return Response(
                {
                    "error": "Failed to fetch metadata from GitHub",
                    "details": r.json(),
                },
                status=r.status_code,
            )

        org_data = r.json()
        github_org_id = org_data.get("id")

        if not is_personal:
            r_member = requests.get(
                f"https://api.github.com/user/memberships/orgs/{github_org_name}",
                headers=headers,
            )
            if r_member.status_code != 200:
                return Response(
                    {"error": f"User is not a member of organization '{github_org_name}' in GitHub."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        org, created = Organization.objects.get_or_create(
            github_org_id=github_org_id,
            defaults={
                "name": org_data.get("name") or org_data.get("login") or github_org_name,
                "github_org_name": github_org_name,
                "avatar_url": org_data.get("avatar_url"),
                "description": (org_data.get("bio") if is_personal else org_data.get("description")),
            },
        )
        if not created:
            org.name = org_data.get("name") or org_data.get("login") or github_org_name
            org.github_org_name = github_org_name
            org.avatar_url = org_data.get("avatar_url")
            org.description = org_data.get("bio") if is_personal else org_data.get("description")
            org.save()

        org.members.add(user)
        if not org.admin:
            org.admin = user
            org.save()

        from organizations.serializers import OrganizationSerializer

        serializer = OrganizationSerializer(org, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GitHubReposViewSet(UserScopedMixin, viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, organization_pk=None):  # noqa: C901
        org = self.get_organization()
        github_org_name = org.github_org_name
        if not github_org_name:
            return Response(
                {"error": "Organization is not linked to GitHub."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        token = user.github_access_token
        if not token:
            from allauth.socialaccount.models import SocialToken

            st = SocialToken.objects.filter(account__user=user, account__provider="github").first()
            if st:
                token = st.token
                user.github_access_token = token
                user.save()
            else:
                return Response(
                    {"error": "GitHub account not linked."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        is_personal = github_org_name.lower() == user.username.lower()
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/json",
        }

        if is_personal:
            url_fetch = "https://api.github.com/user/repos?affiliation=owner&per_page=100"
        else:
            url_fetch = f"https://api.github.com/orgs/{github_org_name}/repos?per_page=100"

        repos = []
        while url_fetch:
            try:
                r = requests.get(url_fetch, headers=headers, timeout=settings.GITHUB_TIMEOUT)
            except requests.exceptions.Timeout:
                return Response(
                    {"error": "Timeout contacting GitHub API."}, status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except requests.exceptions.RequestException:
                return Response(
                    {"error": "Error contacting GitHub API."}, status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            if r.status_code == 401 or r.status_code == 403:
                return Response(
                    {"error": "github_token_invalid", "details": r.json()}, status=status.HTTP_409_CONFLICT
                )

            if r.status_code != 200:
                return Response(
                    {
                        "error": f"Failed to fetch repositories for '{github_org_name}'",
                        "details": r.json(),
                    },
                    status=r.status_code,
                )
            repos.extend(r.json())

            link_header = r.headers.get("Link")
            url_fetch = None
            if link_header:
                links = link_header.split(",")
                for link in links:
                    parts = link.split(";")
                    if len(parts) >= 2 and 'rel="next"' in parts[1]:
                        url_fetch = parts[0].strip()[1:-1]
                        break

        results = []
        for repo in repos:
            results.append(
                {
                    "github_repo_id": repo.get("id"),
                    "github_full_name": repo.get("full_name"),
                    "name": repo.get("name"),
                    "description": repo.get("description"),
                    "url": repo.get("html_url"),
                }
            )
        return Response(results, status=status.HTTP_200_OK)


class GitLabProjectsViewSet(UserScopedMixin, viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, organization_pk=None):
        self.get_organization()

        user = request.user
        token = user.gitlab_access_token
        if not token:
            from allauth.socialaccount.models import SocialToken

            st = SocialToken.objects.filter(account__user=user, account__provider="gitlab").first()
            if st:
                token = st.token
                user.gitlab_access_token = token
                user.save()
                st.delete()
            else:
                return Response(
                    {"error": "GitLab account not linked."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        namespace_id = request.query_params.get("namespace_id")
        if not namespace_id:
            return Response(
                {"error": "namespace_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        kind = request.query_params.get("kind", "group")
        page = request.query_params.get("page", 1)
        search = request.query_params.get("search")

        if kind == "user":
            url = f"https://gitlab.com/api/v4/users/{namespace_id}/projects"
        else:
            url = f"https://gitlab.com/api/v4/groups/{namespace_id}/projects"

        params = {
            "per_page": 50,
            "page": page,
        }
        if search:
            params["search"] = search

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        timeout = getattr(settings, "GITLAB_TIMEOUT", 10)

        try:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
        except requests.exceptions.Timeout:
            return Response(
                {"error": "gitlab_timeout", "details": "Timeout contacting GitLab API."},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.exceptions.RequestException:
            return Response(
                {"error": "gitlab_unavailable", "details": "Error contacting GitLab API."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return self._build_response(r)

    @staticmethod
    def _build_response(r):
        if r.status_code in (401, 403):
            return Response(
                {"error": "gitlab_token_invalid", "details": r.json() if r.content else {}},
                status=status.HTTP_409_CONFLICT,
            )

        if r.status_code != 200:
            return Response(
                {
                    "error": "Failed to fetch projects from GitLab",
                    "details": r.json() if r.content else {},
                },
                status=r.status_code,
            )

        projects = r.json()
        results = []
        if isinstance(projects, list):
            for item in projects:
                results.append(
                    {
                        "gitlab_project_id": item.get("id"),
                        "gitlab_path_with_namespace": item.get("path_with_namespace"),
                        "name": item.get("name"),
                        "description": item.get("description") or "",
                        "url": item.get("web_url"),
                    }
                )

        response = Response(results, status=status.HTTP_200_OK)
        if "X-Total-Pages" in r.headers:
            response["X-Total-Pages"] = str(r.headers["X-Total-Pages"])
        if "X-Next-Page" in r.headers:
            response["X-Next-Page"] = str(r.headers["X-Next-Page"])
        if "X-Page" in r.headers:
            response["X-Page"] = str(r.headers["X-Page"])
        if "X-Total" in r.headers:
            response["X-Total"] = str(r.headers["X-Total"])
        return response
