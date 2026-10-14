from datetime import timedelta
from unittest import mock

from django.utils import timezone

from characteristics.models import CalculatedCharacteristic
from goals.models import Goal
from releases.jobs import get_releases_and_create_results
from releases.models import Release
from utils.tests import APITestCaseExpanded

CORE_RESULT = {
    "characteristics": [
        {"key": "reliability", "value": 0.7},
        {"key": "maintainability", "value": 0.4},
    ]
}


@mock.patch("releases.jobs.calculate_characteristics", return_value=CORE_RESULT)
class GetReleasesAndCreateResultsTestCase(APITestCaseExpanded):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.repository = self.get_repository(self.product)
        self.goal = Goal.objects.create(
            created_by=self.user,
            product=self.product,
            data={"reliability": 50, "maintainability": 50},
        )

    def create_release(self, end_at, repositories=None):
        release = Release.objects.create(
            release_name="Release teste",
            start_at=end_at - timedelta(days=7),
            end_at=end_at,
            created_by=self.user,
            product=self.product,
            goal=self.goal,
        )
        if repositories:
            release.repositories.set(repositories)
        return release

    def test_does_nothing_when_no_release_ends_today(self, core):
        self.create_release(end_at=timezone.now() - timedelta(days=3))

        get_releases_and_create_results()

        core.assert_not_called()
        self.assertFalse(CalculatedCharacteristic.objects.exists())

    def test_creates_results_for_release_repositories(self, core):
        release = self.create_release(end_at=timezone.now(), repositories=[self.repository])

        with self.assertLogs("releases.jobs", level="INFO") as logs:
            get_releases_and_create_results()

        results = CalculatedCharacteristic.objects.filter(release=release, repository=self.repository)
        self.assertEqual(
            {(r.characteristic.key, r.value) for r in results},
            {("reliability", 0.7), ("maintainability", 0.4)},
        )
        self.assertIn("Características calculadas criadas", logs.output[0])

    def test_uses_product_repositories_when_release_has_none(self, core):
        other_repository = self.get_repository(self.product, name="Outro Repositorio")
        release = self.create_release(end_at=timezone.now())

        get_releases_and_create_results()

        self.assertEqual(
            set(CalculatedCharacteristic.objects.filter(release=release).values_list("repository_id", flat=True)),
            {self.repository.id, other_repository.id},
        )

    def test_logs_exception_when_bulk_create_fails(self, core):
        self.create_release(end_at=timezone.now(), repositories=[self.repository])

        with (
            mock.patch.object(CalculatedCharacteristic.objects, "bulk_create", side_effect=Exception("falhou")),
            self.assertLogs("releases.jobs", level="ERROR") as logs,
        ):
            get_releases_and_create_results()

        self.assertIn("Erro ao criar as características calculadas", logs.output[0])
        self.assertFalse(CalculatedCharacteristic.objects.exists())
