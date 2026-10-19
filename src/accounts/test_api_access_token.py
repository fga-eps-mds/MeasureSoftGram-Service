from importlib import import_module

from django.apps import apps
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from accounts.models import ApiAccessToken, CustomUser

copy_session_tokens = import_module("accounts.migrations.0005_apiaccesstoken").copy_session_tokens


class ApiAccessTokenTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="octo", email="octo@example.com", password="secret")
        self.session_token = Token.objects.create(user=self.user)
        self.client = APIClient()

    def authenticate(self, key):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

    def fetch_access_token(self):
        self.authenticate(self.session_token.key)
        response = self.client.get(reverse("api-token-retrieve"))
        self.assertEqual(response.status_code, 200)
        return response.json()["key"]

    def test_access_token_is_not_the_session_token(self):
        key = self.fetch_access_token()

        self.assertNotEqual(key, self.session_token.key)
        self.assertEqual(key, ApiAccessToken.objects.get(user=self.user).key)

    def test_access_token_is_stable_between_requests(self):
        self.assertEqual(self.fetch_access_token(), self.fetch_access_token())

    def test_access_token_keeps_a_provided_key(self):
        key = "a" * 40

        token = ApiAccessToken.objects.create(user=self.user, key=key)

        self.assertEqual(token.key, key)

    def test_access_token_keeps_working_after_logout(self):
        key = self.fetch_access_token()

        self.authenticate(self.session_token.key)
        self.assertEqual(self.client.delete(reverse("accounts-logout")).status_code, 204)

        self.assertEqual(self.client.get(reverse("accounts-retrieve")).status_code, 401)
        self.authenticate(key)
        self.assertEqual(self.client.get(reverse("accounts-retrieve")).status_code, 200)

    def test_access_token_of_inactive_user_is_rejected(self):
        key = self.fetch_access_token()
        self.user.is_active = False
        self.user.save()

        self.authenticate(key)

        self.assertEqual(self.client.get(reverse("accounts-retrieve")).status_code, 401)

    def test_unknown_token_is_rejected(self):
        self.authenticate("0" * 40)

        self.assertEqual(self.client.get(reverse("accounts-retrieve")).status_code, 401)


class CopySessionTokensMigrationTests(TestCase):
    def test_existing_session_tokens_become_access_tokens(self):
        # Quem ja colou o token na GitHub Action continua autenticando depois do deploy.
        user = CustomUser.objects.create_user(username="octo", email="octo@example.com", password="secret")
        session_token = Token.objects.create(user=user)

        copy_session_tokens(apps, None)

        self.assertEqual(ApiAccessToken.objects.get(user=user).key, session_token.key)
