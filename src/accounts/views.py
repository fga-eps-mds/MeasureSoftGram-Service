import contextlib

import requests
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.gitlab.views import GitLabOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache

from accounts.models import ApiAccessToken, CustomUser
from accounts.serializers import (
    AccountsCreateSerializer,
    AccountsLoginSerializer,
    AccountsRetrieveSerializer,
    APIAcessTokenRetrieveSerializer,
    GitHubAccessTokenRetrieveSerializer,
    UserListSerializer,
)

JSON_CONTENT_TYPE = "application/json"


class GithubLoginViewSet(SocialLoginView):
    """
    ViewSet para login via OAuth2 do Github
    """

    adapter_class = GitHubOAuth2Adapter
    permission_classes = (AllowAny,)
    callback_url = settings.LOGIN_REDIRECT_URL
    client_class = OAuth2Client


class GitlabLoginViewSet(SocialLoginView):
    """
    ViewSet para login via OAuth2 do GitLab
    """

    adapter_class = GitLabOAuth2Adapter
    permission_classes = (AllowAny,)
    callback_url = settings.LOGIN_REDIRECT_URL
    client_class = OAuth2Client


class CreateAccountViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    ViewSet para criação de conta
    """

    queryset = CustomUser.objects.all()
    serializer_class = AccountsCreateSerializer
    permission_classes = (AllowAny,)


class RetrieveAccountViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    ViewSet para recuperar informações de conta
    """

    permission_classes = (IsAuthenticated,)

    serializer_class = AccountsRetrieveSerializer

    def get_object(self):
        return self.request.user


class LoginViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    ViewSet para login de conta
    """

    queryset = CustomUser.objects.all()
    serializer_class = AccountsLoginSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response({"key": result.key}, status=status.HTTP_200_OK)


class LogoutViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    ViewSet para logout de conta
    """

    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RetrieveAPIAcessTokenViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    ViewSet para recuperar o token de acesso da conta do usuário, o token vai ser utilizado na github action
    """

    permission_classes = (IsAuthenticated,)

    serializer_class = APIAcessTokenRetrieveSerializer

    def get_object(self):
        token, _ = ApiAccessToken.objects.get_or_create(user=self.request.user)
        return token


class UserListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar todos os usuários
    """

    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    permission_classes = (IsAuthenticated,)


class UserRepos(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para os repositórios do github do user a partir de seu code
    """

    permission_classes = (IsAuthenticated,)

    serializer_class = GitHubAccessTokenRetrieveSerializer

    def retrieve(self, request):
        code = request.query_params.get("code")

        headers = {"Accept": JSON_CONTENT_TYPE}

        urlToken = "https://github.com/login/oauth/access_token"
        data = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_SECRET,
            "code": code,
            "redirect_uri": settings.LOGIN_REDIRECT_URL,
        }
        response = requests.post(urlToken, data=data, headers=headers)
        token_data = response.json()
        if "access_token" not in token_data:
            return Response(
                {
                    "error": "Falha na autenticação do GitHub",
                    "details": token_data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        headersUser = {"Authorization": f'Bearer {token_data["access_token"]}'}
        urlRepos = "https://api.github.com/user/repos?per_page=100"
        responseRepos = requests.get(urlRepos, headers=headersUser)
        repos_data = responseRepos.json()
        formatted_response = {
            "total_count": (len(repos_data) if isinstance(repos_data, list) else 0),
            "items": repos_data if isinstance(repos_data, list) else [],
        }

        return Response(formatted_response, status=status.HTTP_200_OK)


class GitHubOrganizationsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_token(self, user):
        token = user.github_access_token
        if token:
            return token, None
        from allauth.socialaccount.models import SocialToken

        st = SocialToken.objects.filter(account__user=user, account__provider="github").first()
        if not st:
            return None, Response(
                {"error": "GitHub account not linked or access token missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = st.token
        user.github_access_token = token
        user.save()
        st.delete()
        return token, None

    def _fetch_github(self, url, headers, timeout, follow_next=False):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
        except requests.exceptions.Timeout:
            return None, Response(
                {"error": "Timeout contacting GitHub API."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except requests.exceptions.RequestException:
            return None, Response(
                {"error": "Error contacting GitHub API."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if r.status_code in (401, 403):
            details = {}
            with contextlib.suppress(Exception):
                details = r.json()
            return None, Response(
                {"error": "github_token_invalid", "details": details},
                status=status.HTTP_409_CONFLICT,
            )

        if r.status_code != 200:
            details = {}
            with contextlib.suppress(Exception):
                details = r.json()
            return None, Response(
                {"error": "Failed to fetch organizations from GitHub", "details": details},
                status=r.status_code,
            )

        if not follow_next:
            return r.json(), None

        # listas do GitHub vêm em páginas: segue o rel="next" do header Link até a última
        items = list(r.json())
        next_url = (r.links or {}).get("next", {}).get("url")
        if isinstance(next_url, str) and next_url:
            next_items, err = self._fetch_github(next_url, headers, timeout, follow_next=True)
            if err:
                return None, err
            items.extend(next_items)
        return items, None

    def list(self, request):
        token, err = self._get_token(request.user)
        if err:
            return err

        headers = {
            "Authorization": f"token {token}",
            "Accept": JSON_CONTENT_TYPE,
        }
        timeout = getattr(settings, "GITHUB_TIMEOUT", 10)
        results = []

        user_data, user_err = self._fetch_github("https://api.github.com/user", headers, timeout)
        if user_err:
            return user_err

        results.append(
            {
                "github_org_id": user_data.get("id"),
                "github_org_name": user_data.get("login"),
                "avatar_url": user_data.get("avatar_url"),
                "description": "Personal account",
            }
        )

        orgs_data, orgs_err = self._fetch_github(
            "https://api.github.com/user/orgs?per_page=100", headers, timeout, follow_next=True
        )
        if orgs_err and (orgs_err.status_code == status.HTTP_409_CONFLICT or not results):
            return orgs_err

        if orgs_data:
            existing_ids = {x["github_org_id"] for x in results}
            for org in orgs_data:
                if org.get("id") not in existing_ids:
                    results.append(
                        {
                            "github_org_id": org.get("id"),
                            "github_org_name": org.get("login"),
                            "avatar_url": org.get("avatar_url"),
                            "description": org.get("description"),
                        }
                    )
                    existing_ids.add(org.get("id"))

        return Response(results, status=status.HTTP_200_OK)


class GitLabNamespacesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
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

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": JSON_CONTENT_TYPE,
        }
        timeout = getattr(settings, "GITLAB_TIMEOUT", 10)

        from concurrent.futures import ThreadPoolExecutor

        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_user = executor.submit(
                    requests.get,
                    "https://gitlab.com/api/v4/user",
                    headers=headers,
                    timeout=timeout,
                )
                future_groups = executor.submit(self._fetch_all_groups, headers, timeout)
                r_user = future_user.result()
                r_groups = future_groups.result()
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

        return self._build_response(r_user, r_groups)

    @staticmethod
    def _fetch_all_groups(headers, timeout):
        """Segue o X-Next-Page de /groups até o fim; a resposta devolvida leva todos os itens em `all_groups`."""
        base_url = "https://gitlab.com/api/v4/groups?min_access_level=10&per_page=100"
        response = requests.get(base_url, headers=headers, timeout=timeout)
        groups = []
        current = response
        while current.status_code == 200:
            page_data = current.json()
            if isinstance(page_data, list):
                groups.extend(page_data)
            next_page = current.headers.get("X-Next-Page")
            if not (isinstance(next_page, str) and next_page.isdigit()):
                break
            current = requests.get(f"{base_url}&page={next_page}", headers=headers, timeout=timeout)
        if current.status_code != 200:
            return current
        response.all_groups = groups
        return response

    @classmethod
    def _build_response(cls, r_user, r_groups):
        error_response = cls._gitlab_error_response(r_user, r_groups)
        if error_response is not None:
            return error_response

        results = [cls._serialize_gitlab_user(r_user.json())]
        groups_data = getattr(r_groups, "all_groups", None)
        if not isinstance(groups_data, list):
            groups_data = r_groups.json()
        if isinstance(groups_data, list):
            results.extend(cls._serialize_gitlab_group(group) for group in groups_data)

        return Response(results, status=status.HTTP_200_OK)

    @staticmethod
    def _gitlab_error_response(r_user, r_groups):
        """Resposta de erro quando o GitLab recusa o token ou falha; None quando os dois pedidos deram certo."""
        if r_user.status_code in (401, 403) or r_groups.status_code in (401, 403):
            bad_resp = r_user if r_user.status_code in (401, 403) else r_groups
            details = {}
            try:
                details = bad_resp.json()
            except Exception:
                pass
            return Response(
                {"error": "gitlab_token_invalid", "details": details},
                status=status.HTTP_409_CONFLICT,
            )

        for response, error in (
            (r_user, "Failed to fetch user from GitLab"),
            (r_groups, "Failed to fetch groups from GitLab"),
        ):
            if response.status_code != 200:
                return Response(
                    {"error": error, "details": response.json() if response.content else {}},
                    status=response.status_code,
                )

        return None

    @staticmethod
    def _serialize_gitlab_user(user_data):
        return {
            "id": user_data.get("id"),
            "name": user_data.get("name") or user_data.get("username"),
            "full_path": user_data.get("username"),
            "avatar_url": user_data.get("avatar_url"),
            "description": user_data.get("bio") or "",
            "kind": "user",
        }

    @staticmethod
    def _serialize_gitlab_group(group):
        return {
            "id": group.get("id"),
            "name": group.get("name"),
            "full_path": group.get("full_path") or group.get("path"),
            "avatar_url": group.get("avatar_url"),
            "description": group.get("description") or "",
            "kind": "group",
        }


class GithubValidateView(APIView):
    """
    Endpoint para validar as credenciais do GitHub (Client ID e Client Secret)
    """

    permission_classes = (AllowAny,)  # Verificação pré-login.

    def post(self, request):
        frontend_client_id = request.data.get("client_id")
        backend_client_id = getattr(settings, "GITHUB_CLIENT_ID", "")
        backend_secret = getattr(settings, "GITHUB_SECRET", "")

        if not backend_client_id or not backend_secret:
            return Response(
                {
                    "valid": False,
                    "reason": "Backend GitHub credentials are not configured",
                },
                status=status.HTTP_200_OK,
            )

        if frontend_client_id and frontend_client_id != backend_client_id:
            return Response(
                {
                    "valid": False,
                    "reason": "Client ID mismatch between frontend and backend",
                },
                status=status.HTTP_200_OK,
            )

        try:
            url = f"https://api.github.com/applications/{backend_client_id}/token"
            response = requests.post(
                url,
                json={"access_token": "dummy_verification_token"},
                auth=(backend_client_id, backend_secret),
                timeout=5,
            )

            # Se as credenciais estiverem erradas, a resposta será 401 Unauthorized (Bad credentials).
            # Se forem válidas mas o token dummy não existir, a resposta será 404 Not Found.
            if response.status_code == 401:
                return Response(
                    {
                        "valid": False,
                        "reason": "Invalid GitHub Client ID or Client Secret",
                    },
                    status=status.HTTP_200_OK,
                )

            return Response({"valid": True}, status=status.HTTP_200_OK)
        except Exception:
            # Em caso de erro de rede ou timeout, assume como válido para não bloquear login
            return Response({"valid": True}, status=status.HTTP_200_OK)


class GitlabValidateView(APIView):
    """
    Endpoint para validar as credenciais do GitLab (Client ID e Client Secret)
    """

    permission_classes = (AllowAny,)  # Verificação pré-login.

    def post(self, request):
        frontend_client_id = request.data.get("client_id")
        backend_client_id = getattr(settings, "GITLAB_CLIENT_ID", "")
        backend_secret = getattr(settings, "GITLAB_SECRET", "")

        if not backend_client_id or not backend_secret:
            return Response(
                {
                    "valid": False,
                    "reason": "Backend GitLab credentials are not configured",
                },
                status=status.HTTP_200_OK,
            )

        if frontend_client_id and frontend_client_id != backend_client_id:
            return Response(
                {
                    "valid": False,
                    "reason": "Client ID mismatch between frontend and backend",
                },
                status=status.HTTP_200_OK,
            )

        try:
            url = "https://gitlab.com/oauth/token"
            response = requests.post(
                url,
                data={
                    "client_id": backend_client_id,
                    "client_secret": backend_secret,
                    "code": "dummy_verification_token",
                    "grant_type": "authorization_code",
                    "redirect_uri": getattr(settings, "LOGIN_REDIRECT_URL", ""),
                },
                timeout=5,
            )

            # 401 Unauthorized se o client_id ou client_secret estiverem errados.
            # 400 Bad Request se as credenciais forem válidas mas o código dummy for inválido.
            if response.status_code == 401:
                return Response(
                    {
                        "valid": False,
                        "reason": "Invalid GitLab Client ID or Client Secret",
                    },
                    status=status.HTTP_200_OK,
                )

            return Response({"valid": True}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"valid": True}, status=status.HTTP_200_OK)
