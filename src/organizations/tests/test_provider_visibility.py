from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from organizations.models import Organization, Repository, RepositoryAccess
from organizations.utils import sync_provider_memberships
from utils.tests import APITestCaseExpanded


def _response(body, status_code=200, links=None, headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.links = links or {}
    resp.headers = headers or {}
    resp.content = b"{}"
    resp.json.return_value = body
    return resp


class ProviderVisibilityBase(APITestCaseExpanded):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="owner", password="pass")
        self.user = get_user_model().objects.create_user(username="guest", password="pass")
        self.org = Organization.objects.create(name="Org", github_org_id=10, admin=self.owner)
        self.org.members.add(self.owner)
        self.product = self.org.products.create(name="Prod")
        self.repo = Repository.objects.create(
            name="repo",
            product=self.product,
            platform="github",
            github_repo_id=500,
            github_full_name="org/repo",
        )
        self.other_repo = Repository.objects.create(
            name="other", product=self.product, platform="github", github_repo_id=501, github_full_name="org/other"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user, token=Token.objects.create(user=self.user))

    def repo_url(self, repo):
        return reverse(
            "repository-detail",
            kwargs={"organization_pk": self.org.id, "product_pk": self.product.id, "pk": repo.id},
        )


class SyncProviderMembershipsTestCase(ProviderVisibilityBase):
    def setUp(self):
        super().setUp()
        self.user.github_access_token = "tok"
        self.user.save()

    def _github_get(self, orgs, collaborator):
        def side_effect(url, headers=None, params=None, timeout=None):
            if url.endswith("/user/orgs"):
                return _response(orgs)
            if url.endswith("/user/repos"):
                return _response(collaborator)
            return _response({"id": 999})

        return side_effect

    @patch("organizations.utils.requests.get")
    def test_adds_user_to_provider_orgs(self, mock_get):
        mock_get.side_effect = self._github_get([{"id": 10}], [{"id": 500, "full_name": "org/repo"}])

        sync_provider_memberships(self.user)

        self.assertTrue(self.org.members.filter(pk=self.user.pk).exists())
        # membro da org já vê tudo, então não precisa de acesso por repositório
        self.assertFalse(RepositoryAccess.objects.filter(user=self.user).exists())

    @patch("organizations.utils.requests.get")
    def test_removes_user_from_orgs_left_in_provider(self, mock_get):
        self.org.members.add(self.user)
        mock_get.side_effect = self._github_get([], [])

        sync_provider_memberships(self.user)

        self.assertFalse(self.org.members.filter(pk=self.user.pk).exists())
        self.assertTrue(self.org.members.filter(pk=self.owner.pk).exists())

    @patch("organizations.utils.requests.get")
    def test_collaborator_gets_access_only_to_listed_repo(self, mock_get):
        mock_get.side_effect = self._github_get([], [{"id": 500, "full_name": "org/repo"}])

        sync_provider_memberships(self.user)

        self.assertFalse(self.org.members.filter(pk=self.user.pk).exists())
        self.assertEqual(
            list(RepositoryAccess.objects.filter(user=self.user).values_list("repository_id", flat=True)),
            [self.repo.id],
        )

    @patch("organizations.utils.requests.get")
    def test_provider_failure_keeps_memberships(self, mock_get):
        self.org.members.add(self.user)
        mock_get.return_value = _response({"message": "boom"}, status_code=500)

        sync_provider_memberships(self.user)

        self.assertTrue(self.org.members.filter(pk=self.user.pk).exists())

    @patch("organizations.utils.requests.get")
    def test_gitlab_groups_and_projects(self, mock_get):
        gl_org = Organization.objects.create(name="GL", gitlab_group_id=77)
        gl_product = gl_org.products.create(name="GP")
        gl_repo = Repository.objects.create(
            name="glrepo", product=gl_product, platform="gitlab", gitlab_project_id=900
        )
        self.user.gitlab_access_token = "gl"
        self.user.github_access_token = None
        self.user.save()

        def side_effect(url, headers=None, params=None, timeout=None):
            if url.endswith("/groups"):
                return _response([{"id": 77}])
            return _response([{"id": 900}])

        mock_get.side_effect = side_effect

        sync_provider_memberships(self.user)

        self.assertTrue(gl_org.members.filter(pk=self.user.pk).exists())
        self.assertFalse(RepositoryAccess.objects.filter(user=self.user, repository=gl_repo).exists())


class RepositoryAccessViewsTestCase(ProviderVisibilityBase):
    def setUp(self):
        super().setUp()
        self.user.github_access_token = "tok"
        self.user.save()

    @patch("organizations.access.requests.get")
    def test_non_member_with_provider_access_can_read(self, mock_get):
        mock_get.return_value = _response({"id": 500})

        response = self.client.get(self.repo_url(self.repo))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_get.call_args[0][0], "https://api.github.com/repos/org/repo")
        self.assertTrue(RepositoryAccess.objects.filter(user=self.user, repository=self.repo).exists())

    @patch("organizations.access.requests.get")
    def test_non_member_without_provider_access_gets_404_and_loses_access(self, mock_get):
        RepositoryAccess.objects.create(user=self.user, repository=self.repo)
        RepositoryAccess.objects.filter(user=self.user).update(checked_at="2000-01-01T00:00:00Z")
        mock_get.return_value = _response({"message": "Not Found"}, status_code=404)

        response = self.client.get(self.repo_url(self.repo))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(RepositoryAccess.objects.filter(user=self.user).exists())

    @patch("organizations.access.requests.get")
    def test_recent_access_does_not_call_provider(self, mock_get):
        RepositoryAccess.objects.create(user=self.user, repository=self.repo)

        response = self.client.get(self.repo_url(self.repo))

        self.assertEqual(response.status_code, 200)
        mock_get.assert_not_called()

    def test_access_is_read_only(self):
        RepositoryAccess.objects.create(user=self.user, repository=self.repo)

        patch_response = self.client.patch(self.repo_url(self.repo), {"name": "x"}, format="json")
        delete_response = self.client.delete(self.repo_url(self.repo))

        self.assertIn(patch_response.status_code, (403, 404))
        self.assertIn(delete_response.status_code, (403, 404))
        self.repo.refresh_from_db()
        self.assertEqual(self.repo.name, "repo")

    def test_user_only_sees_released_repository(self):
        RepositoryAccess.objects.create(user=self.user, repository=self.repo)

        orgs = self.client.get(reverse("organization-list"))
        repos = self.client.get(
            reverse("repository-list", kwargs={"organization_pk": self.org.id, "product_pk": self.product.id})
        )

        self.assertEqual([o["id"] for o in orgs.json()["results"]], [self.org.id])
        self.assertEqual([r["id"] for r in repos.json()["results"]], [self.repo.id])

    @patch("organizations.access.requests.get")
    def test_other_repository_of_same_org_is_hidden(self, mock_get):
        RepositoryAccess.objects.create(user=self.user, repository=self.repo)
        mock_get.return_value = _response({"message": "Not Found"}, status_code=404)

        response = self.client.get(self.repo_url(self.other_repo))

        self.assertEqual(response.status_code, 404)


class ImportGitLabGroupTestCase(APITestCaseExpanded):
    def _client(self, username):
        user = get_user_model().objects.create_user(username=username, password="pass")
        user.gitlab_access_token = "gl"
        user.save()
        client = APIClient()
        client.force_authenticate(user, token=Token.objects.create(user=user))
        return user, client

    @patch("organizations.views.requests.get")
    def test_second_user_reuses_same_organization(self, mock_get):
        mock_get.return_value = _response({"id": 77, "name": "Grupo", "avatar_url": None, "description": ""})
        first, first_client = self._client("first")
        _, second_client = self._client("second")
        url = reverse("organizations-import-gitlab-list")

        r1 = first_client.post(url, {"gitlab_group_id": 77}, format="json")
        r2 = second_client.post(url, {"gitlab_group_id": 77}, format="json")

        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)
        self.assertEqual(r1.json()["id"], r2.json()["id"])
        org = Organization.objects.get(gitlab_group_id=77)
        self.assertEqual(set(org.members.values_list("username", flat=True)), {"first", "second"})
        self.assertEqual(org.admin, first)

    @patch("organizations.views.requests.get")
    def test_user_outside_group_is_refused(self, mock_get):
        mock_get.return_value = _response({"message": "404 Group Not Found"}, status_code=404)
        _, client = self._client("outsider")

        response = client.post(reverse("organizations-import-gitlab-list"), {"gitlab_group_id": 77}, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Organization.objects.filter(gitlab_group_id=77).exists())

    def test_requires_group_id(self):
        _, client = self._client("x")
        response = client.post(reverse("organizations-import-gitlab-list"), {}, format="json")
        self.assertEqual(response.status_code, 400)
