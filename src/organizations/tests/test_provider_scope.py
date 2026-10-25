from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from goals.models import Goal
from organizations.models import RepositoryAccess
from organizations.tests.test_provider_visibility import ProviderVisibilityBase, _response
from releases.models import Release

EXPIRED = timedelta(minutes=11)


class CollaboratorProductScopeTestCase(ProviderVisibilityBase):
    """Quem só tem acesso a `repo` enxerga o produto, mas não os dados dos outros repositórios dele."""

    def setUp(self):
        super().setUp()
        RepositoryAccess.objects.create(user=self.user, repository=self.repo)
        self.goal = Goal.objects.create(
            created_by=self.owner, product=self.product, data={"reliability": 70, "maintainability": 60}
        )
        self.release = self.create_release(self.product, self.goal, "v1")
        self.release.repositories.set([self.repo, self.other_repo])
        self.product_url = f"/api/v1/organizations/{self.org.id}/products/{self.product.id}/"
        self.owner_client = APIClient()
        self.owner_client.force_authenticate(self.owner, token=Token.objects.create(user=self.owner))

    def create_release(self, product, goal, name):
        now = timezone.now()
        return Release.objects.create(
            release_name=name,
            start_at=now - timedelta(days=10),
            end_at=now + timedelta(days=10),
            created_by=self.owner,
            product=product,
            goal=goal,
        )

    def other_product_release(self):
        product = self.org.products.create(name="Outro produto")
        goal = Goal.objects.create(
            created_by=self.owner, product=product, data={"reliability": 50, "maintainability": 40}
        )
        return goal, self.create_release(product, goal, "v-outro")

    def test_release_list_hides_ids_of_repositories_without_access(self):
        response = self.client.get(f"{self.product_url}release/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["repositories_ids"] for r in response.json()["results"]], [[self.repo.id]])

    def test_release_dashboard_only_lists_visible_repositories(self):
        response = self.client.get(
            f"{self.product_url}release-dashboard/characteristics/", {"release_id": self.release.id}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["id"] for r in response.json()["repositories"]], [self.repo.id])

    def test_tsqmi_release_history_only_lists_visible_repositories(self):
        url = f"{self.product_url}repositories-tsqmi-release-history/"

        response = self.client.get(url)
        other = self.client.get(url, {"repository_id": self.other_repo.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["id"] for r in response.json()["repositories"]], [self.repo.id])
        self.assertEqual(other.status_code, 404)

    def test_entity_matrix_only_lists_visible_repositories(self):
        response = self.client.get(
            f"{self.product_url}entity-analysis/matrix/", {"release_id": self.release.id, "level": "characteristic"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["id"] for r in response.json()["repositories"]], [self.repo.id])

    def test_analysis_distribution_refuses_repository_without_access(self):
        response = self.client.get(
            f"{self.product_url}analysis-distribution/",
            {"release_id": self.release.id, "level": "tsqmi", "repository_id": self.other_repo.id},
        )

        self.assertEqual(response.status_code, 404)

    def test_correlation_refuses_repository_without_access(self):
        response = self.client.get(f"{self.product_url}correlation/", {"repository_id": self.other_repo.id})

        self.assertEqual(response.status_code, 404)

    def test_release_calculations_ignore_repositories_without_access(self):
        for action in ("analysis_data", "planeed-x-accomplished"):
            url = f"{self.product_url}release/{self.release.id}/{action}/"
            with self.subTest(action=action):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotIn(self.other_repo.id, response.json()["release"]["repositories"])

    def test_release_calculations_refuse_release_of_another_product(self):
        _, release = self.other_product_release()
        for action in ("analysis_data", "planeed-x-accomplished"):
            url = f"{self.product_url}release/{release.id}/{action}/"
            with self.subTest(action=action):
                self.assertEqual(self.owner_client.get(url).status_code, 404)

    def test_update_end_at_refuses_release_of_another_product(self):
        _, release = self.other_product_release()
        original_end = release.end_at

        response = self.owner_client.put(
            f"{self.product_url}release/{release.id}/update-end-at/",
            {"end_at": "2030-01-01T00:00:00Z"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        release.refresh_from_db()
        self.assertEqual(release.end_at, original_end)

    def test_update_end_at_is_closed_to_non_members(self):
        original_end = self.release.end_at

        response = self.client.put(
            f"{self.product_url}release/{self.release.id}/update-end-at/",
            {"end_at": "2030-01-01T00:00:00Z"},
            format="json",
        )

        self.assertIn(response.status_code, (403, 404))
        self.release.refresh_from_db()
        self.assertEqual(self.release.end_at, original_end)

    def test_update_end_at_still_works_for_members(self):
        response = self.owner_client.put(
            f"{self.product_url}release/{self.release.id}/update-end-at/",
            {"end_at": "2030-01-01T00:00:00Z"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

    def test_compare_goals_ignores_goal_of_another_product(self):
        goal, _ = self.other_product_release()

        url = reverse("all-goal-list", kwargs={"organization_pk": self.org.id, "product_pk": self.product.id})

        response = self.owner_client.get(url, {"release_id": goal.id})

        # o goal é de outro produto: sem goals no produto da URL, a resposta é a de "produto sem goal"
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "This product does not have a goal.")


class ExpiredAccessListingTestCase(ProviderVisibilityBase):
    """O TTL do acesso vale nas listagens: vencido, só volta se o provedor ainda liberar."""

    def setUp(self):
        super().setUp()
        self.user.github_access_token = "tok"
        self.user.save()
        self.access = RepositoryAccess.objects.create(user=self.user, repository=self.repo)
        RepositoryAccess.objects.filter(pk=self.access.pk).update(checked_at=timezone.now() - EXPIRED)

    def list_organizations(self):
        return self.client.get(reverse("organization-list")).json()["results"]

    def repository_list(self):
        return self.client.get(
            reverse("repository-list", kwargs={"organization_pk": self.org.id, "product_pk": self.product.id})
        )

    @patch("organizations.utils.requests.get")
    def test_expired_access_is_renewed_when_provider_still_grants_it(self, mock_get):
        mock_get.return_value = _response([{"id": 500, "full_name": "org/repo"}])

        orgs = self.list_organizations()

        self.assertEqual([o["id"] for o in orgs], [self.org.id])
        self.access.refresh_from_db()
        self.assertLess(timezone.now() - self.access.checked_at, EXPIRED)

    @patch("organizations.utils.requests.get")
    def test_expired_access_is_removed_when_provider_revoked_it(self, mock_get):
        mock_get.return_value = _response([])

        self.assertEqual(self.list_organizations(), [])
        self.assertFalse(RepositoryAccess.objects.filter(pk=self.access.pk).exists())

    @patch("organizations.utils.requests.get")
    def test_expired_access_stays_hidden_when_provider_fails(self, mock_get):
        mock_get.return_value = _response({"message": "boom"}, status_code=500)

        self.assertEqual(self.list_organizations(), [])
        self.assertTrue(RepositoryAccess.objects.filter(pk=self.access.pk).exists())

    @patch("organizations.utils.requests.get")
    def test_repository_list_hides_revoked_access(self, mock_get):
        mock_get.return_value = _response([])

        self.assertEqual(self.repository_list().status_code, 404)
        self.assertFalse(RepositoryAccess.objects.filter(pk=self.access.pk).exists())

    @patch("organizations.utils.requests.get")
    def test_provider_is_asked_once_per_request(self, mock_get):
        mock_get.return_value = _response([{"id": 500, "full_name": "org/repo"}])

        response = self.repository_list()

        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["id"] for r in response.json()["results"]], [self.repo.id])
        self.assertEqual(mock_get.call_count, 1)

    def test_member_does_not_depend_on_access_ttl(self):
        RepositoryAccess.objects.all().delete()
        self.org.members.add(self.user)

        self.assertEqual([o["id"] for o in self.list_organizations()], [self.org.id])
