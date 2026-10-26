from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from organizations.models import Organization
from utils.tests import APITestCaseExpanded


def _page(body, headers=None, links=None):
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = headers or {}
    resp.links = links or {}
    resp.content = b"{}"
    resp.json.return_value = body
    return resp


class ProviderListingTestCase(APITestCaseExpanded):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="dev", password="pass")
        self.user.github_access_token = "gh"
        self.user.gitlab_access_token = "gl"
        self.user.save()
        self.org = Organization.objects.create(name="Dev", github_org_name="dev")
        self.org.members.add(self.user)
        self.client = APIClient()
        self.client.force_authenticate(self.user, token=Token.objects.create(user=self.user))

    @patch("accounts.views.requests.get")
    def test_gitlab_groups_follow_every_page(self, mock_get):
        def side_effect(url, headers=None, timeout=None):
            if "api/v4/user" in url:
                return _page({"id": 1, "username": "dev"})
            if "page=2" in url:
                return _page([{"id": 2, "name": "G2", "full_path": "g2"}])
            return _page([{"id": 1, "name": "G1", "full_path": "g1"}], headers={"X-Next-Page": "2"})

        mock_get.side_effect = side_effect

        response = self.client.get(reverse("gitlab-namespaces"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [1, 1, 2])
        group_urls = [c[0][0] for c in mock_get.call_args_list if "/groups" in c[0][0]]
        self.assertTrue(all("min_access_level=10" in url and "per_page=100" in url for url in group_urls))

    @patch("organizations.views.requests.get")
    def test_gitlab_personal_space_lists_member_projects(self, mock_get):
        mock_get.return_value = _page([{"id": 5, "name": "p", "path_with_namespace": "x/p", "web_url": "u"}])

        url = reverse("gitlab-projects-list", kwargs={"organization_pk": self.org.id})
        response = self.client.get(url, {"namespace_id": 1, "kind": "user", "search": "p"})

        self.assertEqual(response.status_code, 200)
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://gitlab.com/api/v4/projects")
        self.assertEqual(kwargs["params"]["membership"], "true")
        self.assertEqual(kwargs["params"]["per_page"], 10)
        self.assertEqual(kwargs["params"]["search"], "p")

    @patch("organizations.views.requests.get")
    def test_github_personal_search_finds_collaborator_repo_on_second_page(self, mock_get):
        first = [{"id": 1, "name": "alpha", "full_name": "me/alpha", "html_url": "u1"}]
        second = [{"id": 2, "name": "msg-collab", "full_name": "other/msg-collab", "html_url": "u2"}]

        def side_effect(url, headers=None, params=None, timeout=None):
            if params["page"] == 2:
                return _page(second)
            return _page(first, links={"last": {"url": "https://api.github.com/user/repos?page=2"}})

        mock_get.side_effect = side_effect

        url = reverse("github-repos-list", kwargs={"organization_pk": self.org.id})
        response = self.client.get(url, {"search": "MSG"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["github_full_name"] for r in response.json()], ["other/msg-collab"])
        self.assertEqual(response["X-Total-Pages"], "1")
        self.assertNotIn("X-Next-Page", response)

    def _imported_product(self):
        product = self.org.products.create(name="Prod")
        product.repositories.create(
            name="alpha", url="https://github.com/dev/alpha", platform="github", github_full_name="dev/alpha"
        )
        return product

    @patch("organizations.views.requests.get")
    def test_github_not_imported_tab_fills_every_page(self, mock_get):
        product = self._imported_product()
        repos = [
            {"id": i, "name": name, "full_name": f"dev/{name}", "html_url": f"https://github.com/dev/{name}"}
            for i, name in enumerate(["alpha"] + [f"repo-{n:02d}" for n in range(12)])
        ]
        mock_get.return_value = _page(repos)

        url = reverse("github-repos-list", kwargs={"organization_pk": self.org.id})
        first = self.client.get(url, {"exclude_product": product.id, "page": 1})
        second = self.client.get(url, {"exclude_product": product.id, "page": 2})

        self.assertEqual(len(first.json()), 10)
        self.assertNotIn("alpha", [repo["name"] for repo in first.json()])
        self.assertEqual(len(second.json()), 2)
        self.assertEqual(first["X-Total-Pages"], "2")
        # a 2ª página vem do cache, sem chamar o GitHub de novo
        self.assertEqual(mock_get.call_count, 1)

    def test_exclude_product_of_another_org_is_404(self):
        other = Organization.objects.create(name="Other")
        product = other.products.create(name="P")

        url = reverse("github-repos-list", kwargs={"organization_pk": self.org.id})
        response = self.client.get(url, {"exclude_product": product.id})

        self.assertEqual(response.status_code, 404)

    @patch("organizations.views.requests.get")
    def test_gitlab_not_imported_tab_excludes_product_projects(self, mock_get):
        product = self.org.products.create(name="GL")
        product.repositories.create(
            name="p1", url="https://gitlab.com/g/p1", platform="gitlab", gitlab_project_id=1
        )
        projects = [
            {"id": i, "name": f"p{i}", "path_with_namespace": f"g/p{i}", "web_url": f"https://gitlab.com/g/p{i}"}
            for i in range(1, 4)
        ]
        mock_get.return_value = _page(projects, headers={"X-Total-Pages": "1"})

        url = reverse("gitlab-projects-list", kwargs={"organization_pk": self.org.id})
        response = self.client.get(url, {"namespace_id": 5, "kind": "group", "exclude_product": product.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([p["gitlab_project_id"] for p in response.json()], [2, 3])
        self.assertEqual(mock_get.call_args[1]["params"]["per_page"], 100)
