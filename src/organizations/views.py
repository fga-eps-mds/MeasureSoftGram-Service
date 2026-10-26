import requests
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from django.core.cache import cache
from django.conf import settings

from organizations.access import fresh_access_q, is_member, visible_repositories
from organizations.mixins import UserScopedMixin
from organizations.utils import (
    GITHUB_REPOS_PER_PAGE,
    GITLAB_PROJECTS_PER_PAGE,
    ProviderResponseError,
    fetch_all_provider_repos,
    github_link_page,
    github_total_pages,
    imported_repository_keys,
    paginate_list,
)
from organizations.models import Organization, Product, Repository
from organizations.serializers import (
    OrganizationSerializer,
    ProductSerializer,
    RepositoriesTSQMIHistorySerializer,
    RepositorySerializer,
    RepositoryTSQMILatestValueSerializer,
)

JSON_CONTENT_TYPE = "application/json"


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
        qs = qs.filter(organization=org)
        if not is_member(self.request.user, org):
            qs = qs.filter(fresh_access_q(self.request.user, "repositories__")).distinct()
        return qs

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
        qs = visible_repositories(product, self.request.user).order_by("-id")
        return qs.select_related("product", "product__organization")

    def get_object(self):
        repository = self.get_repository()
        self.check_object_permissions(self.request, repository)
        return repository


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
        qs = visible_repositories(product, self.request.user)
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
        qs = visible_repositories(product, self.request.user)
        qs = qs.select_related("product", "product__organization").prefetch_related("calculated_tsqmis")
        return qs


class ImportOrganizationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _get_user_token(self, user):
        token = user.github_access_token
        if token:
            return token, None
        from allauth.socialaccount.models import SocialToken

        st = SocialToken.objects.filter(account__user=user, account__provider="github").first()
        if not st:
            return None, Response(
                {"error": "GitHub account not linked."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = st.token
        user.github_access_token = token
        user.save()
        return token, None

    def _fetch_github_metadata(self, url_fetch, headers):
        r = requests.get(url_fetch, headers=headers)
        if r.status_code in (401, 403):
            return None, Response(
                {"error": "github_token_invalid", "details": r.json() if r.content else {}},
                status=status.HTTP_409_CONFLICT,
            )
        if r.status_code != 200:
            return None, Response(
                {"error": "Failed to fetch metadata from GitHub", "details": r.json()},
                status=r.status_code,
            )
        return r.json(), None

    def create(self, request):
        github_org_name = request.data.get("github_org_name")
        if not github_org_name:
            return Response(
                {"error": "github_org_name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        token, token_err = self._get_user_token(user)
        if token_err:
            return token_err

        is_personal = github_org_name.lower() == user.username.lower()
        headers = {
            "Authorization": f"token {token}",
            "Accept": JSON_CONTENT_TYPE,
        }

        url_fetch = "https://api.github.com/user" if is_personal else f"https://api.github.com/orgs/{github_org_name}"
        org_data, fetch_err = self._fetch_github_metadata(url_fetch, headers)
        if fetch_err:
            return fetch_err

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


def get_exclude_product(request, organization):
    """Produto do parâmetro `exclude_product` (aba "A Importar"), dentro da organização da URL; None sem ele."""
    product_id = request.query_params.get("exclude_product")
    if not product_id:
        return None
    return get_object_or_404(Product, id=product_id, organization=organization)


class ImportGitLabGroupViewSet(viewsets.ViewSet):
    """Importa um grupo do GitLab como Organization compartilhada (uma por `gitlab_group_id`)."""

    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        group_id = request.data.get("gitlab_group_id")
        if not group_id:
            return Response({"error": "gitlab_group_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        token = user.gitlab_access_token
        if not token:
            return Response({"error": "GitLab account not linked."}, status=status.HTTP_400_BAD_REQUEST)

        headers = {"Authorization": f"Bearer {token}", "Accept": JSON_CONTENT_TYPE}
        timeout = getattr(settings, "GITLAB_TIMEOUT", 10)
        try:
            r = requests.get(f"https://gitlab.com/api/v4/groups/{group_id}", headers=headers, timeout=timeout)
        except requests.exceptions.RequestException:
            return Response({"error": "gitlab_unavailable"}, status=status.HTTP_502_BAD_GATEWAY)

        if r.status_code in (401, 403):
            return Response({"error": "gitlab_token_invalid"}, status=status.HTTP_409_CONFLICT)
        if r.status_code == 404:
            return Response(
                {"error": "User is not a member of this group in GitLab."}, status=status.HTTP_403_FORBIDDEN
            )
        if r.status_code != 200:
            return Response({"error": "Failed to fetch group from GitLab"}, status=r.status_code)

        group = r.json()
        name = group.get("name") or group.get("full_path") or str(group_id)
        org, created = Organization.objects.get_or_create(
            gitlab_group_id=group.get("id"),
            defaults={
                "name": name,
                "avatar_url": group.get("avatar_url"),
                "description": group.get("description") or "",
            },
        )
        if not created:
            org.name = name
            org.avatar_url = group.get("avatar_url")
            org.save()

        org.members.add(user)
        if not org.admin:
            org.admin = user
            org.save()

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
            "Accept": JSON_CONTENT_TYPE,
        }

        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1
        search = (request.query_params.get("search") or "").strip()

        if is_personal:
            url_fetch = "https://api.github.com/user/repos"
            params = {"affiliation": "owner,collaborator", "sort": "full_name"}
        else:
            url_fetch = f"https://api.github.com/orgs/{github_org_name}/repos"
            params = {"type": "all", "sort": "full_name"}

        exclude_product = get_exclude_product(request, org)
        if search or exclude_product is not None:
            # Busca e "A Importar" filtram a lista inteira no servidor, para toda página ter 10 itens. A Search API
            # do GitHub não serve aqui: ignora forks e repositórios em que a pessoa é só colaboradora.
            return self._filtered_list(user, url_fetch, headers, params, search, exclude_product, page)

        try:
            r = requests.get(
                url_fetch,
                headers=headers,
                params={**params, "per_page": GITHUB_REPOS_PER_PAGE, "page": page},
                timeout=settings.GITHUB_TIMEOUT,
            )
        except requests.exceptions.Timeout:
            return Response({"error": "Timeout contacting GitHub API."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.RequestException:
            return Response({"error": "Error contacting GitHub API."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if r.status_code in (401, 403):
            return Response({"error": "github_token_invalid", "details": r.json()}, status=status.HTTP_409_CONFLICT)

        if r.status_code != 200:
            return Response(
                {"error": f"Failed to fetch repositories for '{github_org_name}'", "details": r.json()},
                status=r.status_code,
            )

        total_pages = github_total_pages(r.links, page)
        next_page = github_link_page(r.links, "next")
        return self._paged_response(r.json(), page, total_pages, next_page)

    def _filtered_list(self, user, url, headers, params, search, exclude_product, page):
        cache_key = f"github-repos:{user.id}:{url}:{sorted(params.items())}"
        try:
            repos = fetch_all_provider_repos("github", url, headers, params, settings.GITHUB_TIMEOUT, cache_key)
        except requests.exceptions.Timeout:
            return Response({"error": "Timeout contacting GitHub API."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.RequestException:
            return Response({"error": "Error contacting GitHub API."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ProviderResponseError as exc:
            if exc.status_code in (401, 403):
                return Response(
                    {"error": "github_token_invalid", "details": exc.details}, status=status.HTTP_409_CONFLICT
                )
            return Response({"error": "Failed to fetch repositories", "details": exc.details}, status=exc.status_code)

        needle = search.lower()
        if needle:
            repos = [repo for repo in repos if needle in (repo.get("name") or "").lower()]
        if exclude_product is not None:
            imported = imported_repository_keys(exclude_product)
            repos = [
                repo
                for repo in repos
                if (repo.get("full_name") or "").lower() not in imported
                and (repo.get("html_url") or "").rstrip("/").lower() not in imported
            ]

        page_items, total_pages, next_page = paginate_list(repos, page, GITHUB_REPOS_PER_PAGE)
        return self._paged_response(page_items, page, total_pages, next_page)

    @staticmethod
    def _paged_response(repos, page, total_pages, next_page):
        results = [
            {
                "github_repo_id": repo.get("id"),
                "github_full_name": repo.get("full_name"),
                "name": repo.get("name"),
                "description": repo.get("description"),
                "url": repo.get("html_url"),
            }
            for repo in repos
        ]
        response = Response(results, status=status.HTTP_200_OK)
        response["X-Page"] = str(page)
        response["X-Total-Pages"] = str(total_pages)
        if next_page:
            response["X-Next-Page"] = str(next_page)
        return response


class GitLabProjectsViewSet(UserScopedMixin, viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, organization_pk=None):  # noqa: C901
        org = self.get_organization()

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
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1
        search = request.query_params.get("search")

        params = {}
        if kind == "user":
            # membership=true inclui projetos em que a pessoa foi convidada, mesmo de grupos dos quais não é membro.
            url = "https://gitlab.com/api/v4/projects"
            params.update({"membership": "true", "simple": "true", "order_by": "path"})
        else:
            url = f"https://gitlab.com/api/v4/groups/{namespace_id}/projects"
        if search:
            params["search"] = search

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": JSON_CONTENT_TYPE,
        }
        timeout = getattr(settings, "GITLAB_TIMEOUT", 10)

        exclude_product = get_exclude_product(request, org)
        if exclude_product is not None:
            return self._not_imported(user, url, headers, params, timeout, exclude_product, page)

        try:
            r = requests.get(
                url,
                headers=headers,
                params={**params, "per_page": GITLAB_PROJECTS_PER_PAGE, "page": page},
                timeout=timeout,
            )
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

    def _not_imported(self, user, url, headers, params, timeout, exclude_product, page):
        """Aba "A Importar": a lista inteira do GitLab sem os projetos do produto, em páginas sempre cheias."""
        cache_key = f"gitlab-projects:{user.id}:{url}:{sorted(params.items())}"
        try:
            projects = fetch_all_provider_repos("gitlab", url, headers, params, timeout, cache_key)
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
        except ProviderResponseError as exc:
            if exc.status_code in (401, 403):
                return Response(
                    {"error": "gitlab_token_invalid", "details": exc.details}, status=status.HTTP_409_CONFLICT
                )
            return Response(
                {"error": "Failed to fetch projects from GitLab", "details": exc.details}, status=exc.status_code
            )

        imported = imported_repository_keys(exclude_product)
        projects = [
            project
            for project in projects
            if f"gitlab:{project.get('id')}" not in imported
            and (project.get("path_with_namespace") or "").lower() not in imported
            and (project.get("web_url") or "").rstrip("/").lower() not in imported
        ]
        page_items, total_pages, next_page = paginate_list(projects, page, GITLAB_PROJECTS_PER_PAGE)
        response = Response(self._serialize_projects(page_items), status=status.HTTP_200_OK)
        response["X-Page"] = str(page)
        response["X-Total-Pages"] = str(total_pages)
        if next_page:
            response["X-Next-Page"] = str(next_page)
        return response

    @staticmethod
    def _serialize_projects(projects):
        return [
            {
                "gitlab_project_id": item.get("id"),
                "gitlab_path_with_namespace": item.get("path_with_namespace"),
                "name": item.get("name"),
                "description": item.get("description") or "",
                "url": item.get("web_url"),
            }
            for item in projects
        ]

    @classmethod
    def _build_response(cls, r):
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
        results = cls._serialize_projects(projects) if isinstance(projects, list) else []

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
