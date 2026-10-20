from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from goals.models import Goal
from metrics.models import CollectedMetric, SupportedMetric
from releases.models import Release
from utils.tests import APITestCaseExpanded


class MetricDistributionEndpointTestCase(APITestCaseExpanded):
    def setUp(self):
        self.client = APIClient()
        self.user = self.get_or_create_test_user()
        self.client.force_authenticate(user=self.user)

        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.api = self.get_repository(self.product, name="api")
        self.web = self.get_repository(self.product, name="web")
        self.now = timezone.now()
        self.release = self.create_release(self.product, "R1")
        self.release.repositories.set([self.api, self.web])
        self.url = f"/api/v1/organizations/{self.org.id}/products/{self.product.id}/metrics-distribution/"

    def create_release(self, product, name):
        goal = Goal.objects.create(
            created_by=self.user,
            product=product,
            data={"reliability": 50, "maintainability": 50},
        )
        return Release.objects.create(
            release_name=name,
            start_at=self.now - timedelta(days=10),
            end_at=self.now + timedelta(days=1),
            created_by=self.user,
            product=product,
            goal=goal,
        )

    def collect(self, repository, key, path, value):
        CollectedMetric.objects.create(
            metric=SupportedMetric.objects.get(key=key),
            value=value,
            path=path,
            qualifier="FIL",
            repository=repository,
            created_at=self.now - timedelta(days=1),
        )

    def test_returns_files_and_summary_of_one_repository(self):
        self.collect(self.api, "coverage", "src/a.py", 80.0)
        self.collect(self.api, "coverage", "src/b.py", 0.0)
        self.collect(self.api, "ncloc", "src/a.py", 120)
        self.collect(self.api, "ncloc", "src/b.py", 0)

        response = self.client.get(
            self.url,
            {"release_id": self.release.id, "metric": "coverage", "repository_id": self.api.id},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["metric"], "coverage")
        self.assertEqual(body["release"]["id"], self.release.id)
        self.assertTrue(body["release"]["end_at"].endswith("-03:00"))
        self.assertTrue(body["repositories"][0]["collected_at"].endswith("-03:00"))
        self.assertEqual(
            body["reference"],
            {"measure": "test_coverage", "min_threshold": 60, "max_threshold": 100},
        )
        self.assertEqual(len(body["repositories"]), 1)
        repository = body["repositories"][0]
        self.assertEqual(repository["repository_id"], self.api.id)
        self.assertEqual(repository["repository_name"], "api")
        self.assertEqual(repository["files"], [{"path": "src/a.py", "value": 80.0}])
        self.assertEqual(repository["excluded_files"], 1)
        self.assertEqual(repository["summary"]["count"], 1)

    def test_without_repository_returns_one_summary_per_repository(self):
        self.collect(self.api, "coverage", "src/a.py", 80.0)

        response = self.client.get(self.url, {"release_id": self.release.id, "metric": "coverage"})

        self.assertEqual(response.status_code, 200)
        repositories = response.json()["repositories"]
        self.assertEqual([r["repository_id"] for r in repositories], [self.api.id, self.web.id])
        self.assertTrue(all("files" not in r for r in repositories))
        self.assertEqual(repositories[0]["summary"]["count"], 1)
        self.assertIsNone(repositories[1]["summary"])
        self.assertIsNone(repositories[1]["collected_at"])

    def test_release_without_repositories_uses_product_repositories(self):
        release = self.create_release(self.product, "R2")

        response = self.client.get(self.url, {"release_id": release.id, "metric": "coverage"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [r["repository_id"] for r in response.json()["repositories"]],
            [self.api.id, self.web.id],
        )

    def test_rejects_metric_not_collected_by_file(self):
        response = self.client.get(self.url, {"release_id": self.release.id, "metric": "total_issues"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("metric", response.json())

    def test_requires_release_and_metric(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 400)
        self.assertIn("release_id", response.json())
        self.assertIn("metric", response.json())

    def test_release_of_another_product_returns_404(self):
        other_release = self.create_release(self.get_product(self.org, name="Outro"), "R1")

        response = self.client.get(self.url, {"release_id": other_release.id, "metric": "coverage"})

        self.assertEqual(response.status_code, 404)

    def test_repository_of_another_product_returns_404(self):
        other_repository = self.get_repository(self.get_product(self.org, name="Outro"), name="x")

        response = self.client.get(
            self.url,
            {"release_id": self.release.id, "metric": "coverage", "repository_id": other_repository.id},
        )

        self.assertEqual(response.status_code, 404)

    def test_non_member_gets_404(self):
        outsider = get_user_model().objects.create(username="outsider", email="outsider@email.com")
        self.client.force_authenticate(user=outsider)

        response = self.client.get(self.url, {"release_id": self.release.id, "metric": "coverage"})

        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_gets_401(self):
        response = APIClient().get(self.url, {"release_id": self.release.id, "metric": "coverage"})

        self.assertEqual(response.status_code, 401)

    def test_ignores_release_repositories_from_another_product(self):
        other_org = self.get_organization(name="Outra organização", add_user=False)
        foreign = self.get_repository(self.get_product(other_org, name="Alheio"), name="alheio")
        self.release.repositories.add(foreign)

        response = self.client.get(self.url, {"release_id": self.release.id, "metric": "coverage"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [r["repository_id"] for r in response.json()["repositories"]],
            [self.api.id, self.web.id],
        )

    def test_repositories_are_ordered_by_name(self):
        first_by_name = self.get_repository(self.product, name="aaa")
        self.release.repositories.add(first_by_name)

        response = self.client.get(self.url, {"release_id": self.release.id, "metric": "coverage"})

        self.assertEqual(
            [r["repository_id"] for r in response.json()["repositories"]],
            [first_by_name.id, self.api.id, self.web.id],
        )
