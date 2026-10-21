from datetime import datetime, timedelta

from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
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

    def test_measures_endpoints_only_read_the_repository_measures(self):
        measure = SupportedMeasure.objects.get(key="test_coverage")
        other_repository = self.get_repository(self.product, name="Outro Repositório")
        for repository in (self.repository, other_repository):
            CalculatedMeasure.objects.create(measure=measure, repository=repository, value=0.5, created_at=day(0))

        for endpoint in (self.url, self.url.replace("historical-values", "latest-values")):
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(f"{endpoint}/measures/")
            self.assertEqual(response.status_code, 200)

            # toda leitura de medidas calculadas é do repositório pedido
            measure_queries = [q["sql"] for q in queries if '"measures_calculatedmeasure"."value"' in q["sql"]]
            self.assertTrue(measure_queries)
            for sql in measure_queries:
                self.assertIn('"measures_calculatedmeasure"."repository_id" =', sql)

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

    def count_queries(self, url):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return len(queries)

    def test_values_endpoints_do_not_query_once_per_entity(self):
        # antes: uma consulta de valores e uma do repositório para cada entidade da lista
        metrics = list(SupportedMetric.objects.order_by("id")[:6])
        measures = list(SupportedMeasure.objects.order_by("id")[:6])
        latest_url = self.url.replace("historical-values", "latest-values")
        urls = [f"{base}/{entity}/" for base in (self.url, latest_url) for entity in ("metrics", "measures")]

        CollectedMetric.objects.create(metric=metrics[0], repository=self.repository, value=1, created_at=day(0))
        CalculatedMeasure.objects.create(measure=measures[0], repository=self.repository, value=0.1, created_at=day(0))
        with_one_entity = [self.count_queries(url) for url in urls]

        for n, (metric, measure) in enumerate(zip(metrics[1:], measures[1:])):
            CollectedMetric.objects.create(metric=metric, repository=self.repository, value=n, created_at=day(n))
            CalculatedMeasure.objects.create(measure=measure, repository=self.repository, value=0.1, created_at=day(n))

        self.assertEqual([self.count_queries(url) for url in urls], with_one_entity)

    def test_latest_value_keeps_the_first_record_of_a_collection(self):
        # uma coleta grava vários registros no mesmo instante; fica o primeiro gravado, como antes
        metric = SupportedMetric.objects.get(key="coverage")
        first = CollectedMetric.objects.create(metric=metric, repository=self.repository, value=70, created_at=day(1))
        CollectedMetric.objects.create(metric=metric, repository=self.repository, value=10, created_at=day(1))
        CollectedMetric.objects.create(metric=metric, repository=self.repository, value=5, created_at=day(0))

        response = self.client.get(f"{self.url.replace('historical-values', 'latest-values')}/metrics/")

        latest = next(item["latest"] for item in response.json()["results"] if item["key"] == "coverage")
        self.assertEqual(latest["id"], first.id)

    def test_latest_metric_value_filters_by_qualifier(self):
        metric = SupportedMetric.objects.get(key="coverage")
        CollectedMetric.objects.create(
            metric=metric, repository=self.repository, value=10, qualifier="FIL", path="a.py", created_at=day(1)
        )
        CollectedMetric.objects.create(
            metric=metric, repository=self.repository, value=70, qualifier="TRK", created_at=day(1)
        )
        latest_url = f"{self.url.replace('historical-values', 'latest-values')}/metrics/"

        def latest(params):
            response = self.client.get(latest_url, params)
            return next(item["latest"] for item in response.json()["results"] if item["key"] == "coverage")

        # sem o parâmetro, como antes: o primeiro registro gravado na coleta, que aqui é o de um arquivo
        self.assertEqual(latest({})["value"], 10)
        self.assertEqual(latest({"qualifier": "TRK"})["value"], 70)

    def test_user_who_is_not_member_cannot_read_history(self):
        outsider = CustomUser.objects.create(username="outsider", email="outsider@example.com")
        client = APIClient()
        client.force_authenticate(outsider, token=Token.objects.create(user=outsider))

        response = client.get(f"{self.url}/characteristics/")

        self.assertEqual(response.status_code, 404)
