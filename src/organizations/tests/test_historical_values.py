from datetime import datetime, timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import CustomUser
from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from measures.models import CalculatedMeasure, SupportedMeasure
from metrics.models import CollectedMetric, SupportedMetric
from subcharacteristics.models import CalculatedSubCharacteristic, SupportedSubCharacteristic
from tsqmi.models import TSQMI
from utils.tests import APITestCaseExpanded

FIRST_DAY = timezone.make_aware(datetime(2026, 3, 1))


def day(n):
    return FIRST_DAY + timedelta(days=n)


@override_settings(MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS=3)
class HistoricalValuesEndpointsTestCase(APITestCaseExpanded):
    """O histórico devolve os registros mais recentes, do mais antigo para o mais novo."""

    def setUp(self):
        self.client = APIClient()
        self.user = self.get_or_create_test_user()
        self.client.force_authenticate(self.user, token=Token.objects.create(user=self.user))

        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.repository = self.get_repository(self.product)
        self.product_url = f"/api/v1/organizations/{self.org.id}/products/{self.product.id}"
        self.url = f"{self.product_url}/repositories/{self.repository.id}/historical-values"

    def history(self, entity, key, params=None):
        response = self.client.get(f"{self.url}/{entity}/", params or {})
        self.assertEqual(response.status_code, 200)
        entry = next(item for item in response.json()["results"] if item["key"] == key)
        return [item["value"] for item in entry["history"]]

    def test_characteristics_history_keeps_the_latest_records(self):
        characteristic = SupportedCharacteristic.objects.get(key="maintainability")
        for n in range(5):
            CalculatedCharacteristic.objects.create(
                characteristic=characteristic, repository=self.repository, value=n / 10, created_at=day(n)
            )

        self.assertEqual(self.history("characteristics", "maintainability"), [0.2, 0.3, 0.4])

    def test_subcharacteristics_history_keeps_the_latest_records(self):
        subcharacteristic = SupportedSubCharacteristic.objects.get(key="modifiability")
        for n in range(5):
            CalculatedSubCharacteristic.objects.create(
                subcharacteristic=subcharacteristic, repository=self.repository, value=n / 10, created_at=day(n)
            )

        self.assertEqual(self.history("subcharacteristics", "modifiability"), [0.2, 0.3, 0.4])

    def test_measures_history_keeps_the_latest_records(self):
        measure = SupportedMeasure.objects.get(key="test_coverage")
        for n in range(5):
            CalculatedMeasure.objects.create(
                measure=measure, repository=self.repository, value=n / 10, created_at=day(n)
            )

        self.assertEqual(self.history("measures", "test_coverage"), [0.2, 0.3, 0.4])

    def test_metrics_history_keeps_the_latest_records(self):
        metric = SupportedMetric.objects.get(key="total_builds")
        for n in range(5):
            CollectedMetric.objects.create(
                metric=metric, repository=self.repository, value=n, qualifier="TRK", created_at=day(n)
            )

        self.assertEqual(self.history("metrics", "total_builds"), [2, 3, 4])

    def test_metrics_history_filters_by_qualifier(self):
        metric = SupportedMetric.objects.get(key="coverage")
        CollectedMetric.objects.create(
            metric=metric, repository=self.repository, value=70, qualifier="TRK", created_at=day(0)
        )
        for n in range(3):
            CollectedMetric.objects.create(
                metric=metric,
                repository=self.repository,
                value=10 + n,
                qualifier="FIL",
                path=f"file_{n}.py",
                created_at=day(1),
            )
        CollectedMetric.objects.create(
            metric=metric, repository=self.repository, value=80, qualifier="TRK", created_at=day(2)
        )

        self.assertEqual(self.history("metrics", "coverage", {"qualifier": "TRK"}), [70, 80])
        # sem o parâmetro, o histórico continua com todos os registros, como antes
        self.assertEqual(len(self.history("metrics", "coverage")), 3)

    def test_repositories_tsqmi_history_keeps_the_latest_records(self):
        for n in range(5):
            TSQMI.objects.create(repository=self.repository, value=n / 10, created_at=day(n))

        response = self.client.get(f"{self.product_url}/repositories-tsqmi-historical-values/")

        self.assertEqual(response.status_code, 200)
        repository = next(item for item in response.json()["results"] if item["id"] == self.repository.id)
        self.assertEqual([item["value"] for item in repository["history"]], [0.2, 0.3, 0.4])

    def test_user_who_is_not_member_cannot_read_history(self):
        outsider = CustomUser.objects.create(username="outsider", email="outsider@example.com")
        client = APIClient()
        client.force_authenticate(outsider, token=Token.objects.create(user=outsider))

        response = client.get(f"{self.url}/characteristics/")

        self.assertEqual(response.status_code, 404)
