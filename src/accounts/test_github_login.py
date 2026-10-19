from unittest.mock import MagicMock, patch

from allauth.socialaccount.models import SocialAccount
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from accounts.models import CustomUser

GITHUB_TOKEN = "gho_fake_token"
GITHUB_UID = 4242
GITHUB_EMAIL = "octocat@example.com"
GITHUB_PROFILE = {"id": GITHUB_UID, "login": "octocat", "name": "Octo Cat", "email": GITHUB_EMAIL}
GITHUB_EMAILS = [{"email": GITHUB_EMAIL, "primary": True, "verified": True}]
VALID_TOKEN_PAYLOAD = {"access_token": GITHUB_TOKEN, "token_type": "bearer"}
EMAIL_CONFLICT_MESSAGE = "O e-mail desta conta do GitHub já está em uso por outro usuário do MeasureSoftGram."


def github_response(payload):
    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": "application/json"}
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def fake_github(token_payload=VALID_TOKEN_PAYLOAD):
    """Simula a troca do code e a API de perfil/e-mails do GitHub."""
    responses = {
        "/login/oauth/access_token": token_payload,
        "/user/emails": GITHUB_EMAILS,
        "/user": GITHUB_PROFILE,
    }

    def request(session, method, url, *args, **kwargs):
        for suffix, payload in responses.items():
            if url.endswith(suffix):
                return github_response(payload)
        raise AssertionError(f"Requisição inesperada para {url}")

    return patch("requests.Session.request", new=request)


class GithubLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("github-login")

    def login(self, code="valid-code", token_payload=VALID_TOKEN_PAYLOAD):
        with fake_github(token_payload):
            return self.client.post(self.url, {"code": code}, format="json")

    def test_first_login_creates_user_and_returns_token(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)
        user = CustomUser.objects.get(email=GITHUB_EMAIL)
        self.assertEqual(response.json(), {"key": Token.objects.get(user=user).key})
        self.assertTrue(SocialAccount.objects.filter(user=user, provider="github", uid=str(GITHUB_UID)).exists())
        self.assertEqual(user.github_access_token, GITHUB_TOKEN)

    def test_second_login_reuses_existing_user(self):
        self.login()
        response = self.login(code="another-code")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.filter(email=GITHUB_EMAIL).count(), 1)

    def test_login_with_email_of_password_account_returns_clear_error(self):
        CustomUser.objects.create_user(username="octo", email=GITHUB_EMAIL, password="secret")

        response = self.login()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"non_field_errors": [EMAIL_CONFLICT_MESSAGE]})
        self.assertFalse(SocialAccount.objects.exists())

    def test_email_conflict_ignores_case(self):
        CustomUser.objects.create_user(username="octo", email=GITHUB_EMAIL.upper(), password="secret")

        response = self.login()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"non_field_errors": [EMAIL_CONFLICT_MESSAGE]})

    def test_email_conflict_keeps_local_password(self):
        user = CustomUser.objects.create_user(username="octo", email=GITHUB_EMAIL, password="secret")

        self.login()

        user.refresh_from_db()
        self.assertTrue(user.check_password("secret"))

    def test_invalid_code_returns_bad_request(self):
        response = self.login(token_payload={"error": "bad_verification_code"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"non_field_errors": ["Failed to exchange code for access token"]})


def fake_gitlab():
    """Simula a troca do code e a API de perfil do GitLab."""
    responses = {
        "/oauth/token": VALID_TOKEN_PAYLOAD,
        "/api/v4/user": {"id": 7, "username": "octolab", "name": "Octo Lab", "email": GITHUB_EMAIL},
    }

    def request(session, method, url, *args, **kwargs):
        for suffix, payload in responses.items():
            if url.endswith(suffix):
                return github_response(payload)
        raise AssertionError(f"Requisição inesperada para {url}")

    return patch("requests.Session.request", new=request)


class GitlabLoginConflictTests(TestCase):
    def test_login_with_email_of_existing_account_names_gitlab(self):
        CustomUser.objects.create_user(username="octo", email=GITHUB_EMAIL, password="secret")

        with fake_gitlab():
            response = APIClient().post(reverse("gitlab-login"), {"code": "valid-code"}, format="json")

        self.assertEqual(response.status_code, 400)
        message = "O e-mail desta conta do GitLab já está em uso por outro usuário do MeasureSoftGram."
        self.assertEqual(response.json(), {"non_field_errors": [message]})
