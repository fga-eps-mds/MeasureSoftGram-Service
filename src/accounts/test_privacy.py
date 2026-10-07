from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import CustomUser


class UserPrivacyTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="alice", email="alice@example.com", password="secret")
        self.other = CustomUser.objects.create_user(username="bob", email="bob@example.com")

    def test_anonymous_users_list_returns_401_without_personal_data(self):
        url = reverse("user-list")
        self.assertEqual(url, "/api/v1/accounts/users/")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(set(response.data), {"detail"})
        self.assertNotIn(self.other.email, response.content.decode())

    def test_authenticated_list_omits_email_and_tokens(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, 200)
        for user in response.data["results"]:
            self.assertEqual(set(user), {"id", "username", "first_name", "last_name"})

    def test_own_profile_keeps_email(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("accounts-retrieve"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertNotIn("github_access_token", response.data)

    def test_default_permissions_protect_previously_public_catalog(self):
        response = self.client.get("/api/v1/supported-characteristics/")
        self.assertEqual(response.status_code, 401)

    def test_github_login_is_reachable_without_authentication(self):
        response = self.client.post(reverse("github-login"), {}, format="json")
        self.assertEqual(response.status_code, 400)  # Missing OAuth code, not authentication denied.
