from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from goals.models import Goal
from measures.models import CalculatedMeasure, SupportedMeasure
from metrics.models import CollectedMetric, SupportedMetric
from releases.analysis_distribution import summarize
from releases.models import Release
from subcharacteristics.models import CalculatedSubCharacteristic, SupportedSubCharacteristic
from tsqmi.models import TSQMI
from utils.tests import APITestCaseExpanded


def local_datetime(*args):
    return timezone.make_aware(datetime(*args))


# Série de referência, para conferir numa planilha (valores em A1:A10):
#   0,55  0,2  0,62  0,49  0,9  0,43  0,66  0,58  0,45  0,52
# Esperado:
#   PERCENTIL.INC(A1:A10; 0,1) = 0,407     QUARTIL.INC(A1:A10; 1) = 0,46
#   QUARTIL.INC(A1:A10; 2)     = 0,535     QUARTIL.INC(A1:A10; 3) = 0,61
#   PERCENTIL.INC(A1:A10; 0,9) = 0,684     MÉDIA(A1:A10)          = 0,54
#   DISTORÇÃO(A1:A10)          = 0,178488933752135
#   IQR = 0,15; limites = 0,235 e 0,835; discrepantes: 0,2 e 0,9
REFERENCE_SERIES = [0.55, 0.2, 0.62, 0.49, 0.9, 0.43, 0.66, 0.58, 0.45, 0.52]


class SummarizeTestCase(SimpleTestCase):
    def assertSummary(self, summary, expected):
        for field, value in expected.items():
            if value is None:
                self.assertIsNone(summary[field], field)
            else:
                self.assertAlmostEqual(summary[field], value, places=12, msg=field)

    def test_reference_series_matches_spreadsheet(self):
        summary = summarize(REFERENCE_SERIES)

        self.assertEqual(summary["count"], 10)
        self.assertEqual(summary["outliers"], 2)
        self.assertSummary(
            summary,
            {
                "min": 0.2,
                "p10": 0.407,
                "q1": 0.46,
                "median": 0.535,
                "q3": 0.61,
                "p90": 0.684,
                "max": 0.9,
                "iqr": 0.15,
                "lower_limit": 0.235,
                "upper_limit": 0.835,
                "mean": 0.54,
                "skewness": 0.178488933752135,
            },
        )

    def test_without_values(self):
        summary = summarize([])

        self.assertEqual(summary["count"], 0)
        self.assertEqual(summary["outliers"], 0)
        for field in ("min", "p10", "q1", "median", "q3", "p90", "max", "iqr", "mean", "skewness"):
            self.assertIsNone(summary[field], field)

    def test_one_value(self):
        summary = summarize([0.7])

        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["outliers"], 0)
        self.assertSummary(
            summary,
            {"min": 0.7, "p10": 0.7, "q1": 0.7, "median": 0.7, "q3": 0.7, "p90": 0.7, "max": 0.7, "iqr": 0},
        )
        self.assertEqual(summary["mean"], 0.7)
        self.assertIsNone(summary["skewness"])

    def test_two_values_have_no_skewness(self):
        # QUARTIL.INC({0,4; 0,8}; 1..3) = 0,5 / 0,6 / 0,7; PERCENTIL.INC 0,1 e 0,9 = 0,44 e 0,76
        summary = summarize([0.8, 0.4])

        self.assertSummary(
            summary,
            {"p10": 0.44, "q1": 0.5, "median": 0.6, "q3": 0.7, "p90": 0.76, "mean": 0.6, "skewness": None},
        )

    def test_three_values_have_skewness(self):
        # QUARTIL.INC({0,1; 0,2; 0,6}; 1..3) = 0,15 / 0,2 / 0,4; DISTORÇÃO = 1,457862967321305
        summary = summarize([0.6, 0.1, 0.2])

        self.assertSummary(
            summary,
            {"p10": 0.12, "q1": 0.15, "median": 0.2, "q3": 0.4, "p90": 0.52, "skewness": 1.457862967321305},
        )

    def test_constant_values_have_no_skewness(self):
        summary = summarize([0.5, 0.5, 0.5])

        self.assertEqual(summary["iqr"], 0)
        self.assertEqual(summary["outliers"], 0)
        self.assertIsNone(summary["skewness"])


class AnalysisDistributionEndpointTestCase(APITestCaseExpanded):
    def setUp(self):
        self.client = APIClient()
        self.user = self.get_or_create_test_user()
        self.client.force_authenticate(self.user, token=Token.objects.create(user=self.user))

        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.api = self.get_repository(self.product, name="api")
        self.web = self.get_repository(self.product, name="web")

        goal = Goal.objects.create(
            created_by=self.user,
            product=self.product,
            data={"reliability": 70, "maintainability": 60},
        )
        self.release = Release.objects.create(
            release_name="R2",
            start_at=local_datetime(2026, 3, 1),
            end_at=local_datetime(2026, 3, 31),
            created_by=self.user,
            product=self.product,
            goal=goal,
        )
        self.url = f"/api/v1/organizations/{self.org.id}/products/{self.product.id}/analysis-distribution/"

    def get(self, level, key=None, repository=None, **params):
        query = {"release_id": self.release.id, "repository_id": (repository or self.api).id, "level": level}
        if key is not None:
            query["key"] = key
        return self.client.get(self.url, {**query, **params})

    def tsqmi(self, value, created_at, repository=None):
        return TSQMI.objects.create(repository=repository or self.api, value=value, created_at=created_at)

    def characteristic(self, key, value, created_at, **fields):
        return CalculatedCharacteristic.objects.create(
            characteristic=SupportedCharacteristic.objects.get(key=key),
            repository=self.api,
            value=value,
            created_at=created_at,
            **fields,
        )

    def subcharacteristic(self, key, value, created_at):
        return CalculatedSubCharacteristic.objects.create(
            subcharacteristic=SupportedSubCharacteristic.objects.get(key=key),
            repository=self.api,
            value=value,
            created_at=created_at,
        )

    def measure(self, key, value, created_at):
        return CalculatedMeasure.objects.create(
            measure=SupportedMeasure.objects.get(key=key),
            repository=self.api,
            value=value,
            created_at=created_at,
        )

    def metric(self, key, value, created_at, qualifier="TRK", path=None):
        return CollectedMetric.objects.create(
            metric=SupportedMetric.objects.get(key=key),
            repository=self.api,
            value=value,
            created_at=created_at,
            qualifier=qualifier,
            path=path,
        )

    def values(self, entity):
        return [analysis["value"] for analysis in entity["analyses"]]

    def test_tsqmi_returns_analyses_in_window_ordered_by_date(self):
        self.tsqmi(0.7, local_datetime(2026, 3, 20, 10))
        self.tsqmi(0.5, local_datetime(2026, 3, 2, 9))
        self.tsqmi(0.6, local_datetime(2026, 3, 31, 18, 30))
        # fora da janela e de outro repositório
        self.tsqmi(0.1, local_datetime(2026, 2, 28, 23))
        self.tsqmi(0.9, local_datetime(2026, 4, 1, 8))
        self.tsqmi(0.3, local_datetime(2026, 3, 10), repository=self.web)

        response = self.get("tsqmi")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["release"]["id"], self.release.id)
        self.assertEqual(data["release"]["release_name"], "R2")
        self.assertTrue(data["release"]["end_at"].endswith("-03:00"))
        self.assertEqual(data["repository"], {"id": self.api.id, "name": "api"})
        self.assertEqual((data["level"], data["key"]), ("tsqmi", "tsqmi"))
        self.assertEqual(
            data["period"],
            {"count": 3, "first": "2026-03-02T09:00:00-03:00", "last": "2026-03-31T18:30:00-03:00"},
        )
        entity = data["entity"]
        self.assertEqual(
            (entity["key"], entity["name"], entity["level"], entity["metric_type"]),
            ("tsqmi", "TSQMI", "tsqmi", None),
        )
        self.assertEqual(self.values(entity), [0.5, 0.7, 0.6])
        self.assertEqual(entity["analyses"][0]["date"], "2026-03-02T09:00:00-03:00")
        self.assertEqual(entity["summary"]["count"], 3)

    def test_tsqmi_children_are_characteristics_with_analyses_in_configuration_order(self):
        self.tsqmi(0.6, local_datetime(2026, 3, 5))
        self.characteristic("maintainability", 0.4, local_datetime(2026, 3, 5))
        self.characteristic("reliability", 0.8, local_datetime(2026, 3, 5))
        self.characteristic("reliability", 0.7, local_datetime(2026, 3, 6))

        children = self.get("tsqmi").json()["children"]

        # functional_suitability, sem análise, fica fora
        self.assertEqual([child["key"] for child in children], ["reliability", "maintainability"])
        self.assertEqual(children[0]["level"], "characteristic")
        self.assertEqual(self.values(children[0]), [0.8, 0.7])
        self.assertEqual(children[0]["summary"]["count"], 2)

    def test_characteristic_children_are_subcharacteristics(self):
        self.characteristic("reliability", 0.55, local_datetime(2026, 3, 5))
        self.subcharacteristic("maturity", 0.3, local_datetime(2026, 3, 5))
        self.subcharacteristic("testing_status", 0.6, local_datetime(2026, 3, 5))
        # de outra característica
        self.subcharacteristic("modifiability", 0.9, local_datetime(2026, 3, 5))

        data = self.get("characteristic", "reliability").json()

        self.assertEqual(data["entity"]["name"], SupportedCharacteristic.objects.get(key="reliability").name)
        self.assertEqual(self.values(data["entity"]), [0.55])
        self.assertEqual([child["key"] for child in data["children"]], ["testing_status", "maturity"])

    def test_subcharacteristic_children_are_measures(self):
        self.subcharacteristic("testing_status", 0.6, local_datetime(2026, 3, 5))
        self.measure("test_coverage", 0.5, local_datetime(2026, 3, 5))
        self.measure("passed_tests", 1.0, local_datetime(2026, 3, 5))

        data = self.get("subcharacteristic", "testing_status").json()

        self.assertEqual([child["key"] for child in data["children"]], ["passed_tests", "test_coverage"])
        self.assertEqual(data["children"][0]["level"], "measure")

    def test_measure_children_are_project_level_metrics_with_type(self):
        self.measure("ci_feedback_time", 0.4, local_datetime(2026, 3, 5))
        self.metric("total_builds", 10, local_datetime(2026, 3, 5))
        self.metric("sum_ci_feedback_times", 3000, local_datetime(2026, 3, 5))

        data = self.get("measure", "ci_feedback_time").json()

        children = {child["key"]: child for child in data["children"]}
        self.assertEqual(set(children), {"total_builds", "sum_ci_feedback_times"})
        self.assertEqual(children["total_builds"]["level"], "metric")
        self.assertEqual(
            children["total_builds"]["metric_type"], SupportedMetric.objects.get(key="total_builds").metric_type
        )
        self.assertIsNone(data["entity"]["metric_type"])

    def test_measure_without_project_level_metric_has_no_children(self):
        self.measure("test_coverage", 0.5, local_datetime(2026, 3, 5))
        # coverage é gravada por arquivo, sem valor por análise
        self.metric("coverage", 80.0, local_datetime(2026, 3, 5), qualifier="FIL", path="src/a.py")

        data = self.get("measure", "test_coverage").json()

        self.assertEqual(self.values(data["entity"]), [0.5])
        self.assertEqual(data["children"], [])

    def test_metric_returns_project_level_values_and_no_children(self):
        self.metric("total_builds", 10, local_datetime(2026, 3, 5))
        self.metric("total_builds", 14, local_datetime(2026, 3, 9))

        response = self.get("metric", "total_builds")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["entity"]["metric_type"], SupportedMetric.objects.get(key="total_builds").metric_type)
        self.assertEqual(self.values(data["entity"]), [10, 14])
        self.assertEqual(data["children"], [])

    def test_sonarqube_metric_is_rejected(self):
        self.metric("coverage", 80.0, local_datetime(2026, 3, 5), qualifier="FIL", path="src/a.py")

        response = self.get("metric", "coverage")

        self.assertEqual(response.status_code, 400)

    def test_release_closing_rows_are_not_analyses(self):
        self.characteristic("reliability", 0.6, local_datetime(2026, 3, 5))
        # linha do fechamento da release, dentro da mesma janela
        self.characteristic("reliability", 0.1, local_datetime(2026, 3, 31, 12), release=self.release)

        data = self.get("characteristic", "reliability").json()

        self.assertEqual(self.values(data["entity"]), [0.6])
        self.assertEqual(data["period"]["count"], 1)

    def test_release_closing_rows_are_not_children_analyses(self):
        self.tsqmi(0.6, local_datetime(2026, 3, 5))
        self.characteristic("reliability", 0.1, local_datetime(2026, 3, 31, 12), release=self.release)

        self.assertEqual(self.get("tsqmi").json()["children"], [])

    def test_summary_and_outliers_of_reference_series(self):
        for day, value in enumerate(REFERENCE_SERIES, start=1):
            self.tsqmi(value, local_datetime(2026, 3, day))

        entity = self.get("tsqmi").json()["entity"]

        summary = entity["summary"]
        self.assertEqual(summary["count"], 10)
        self.assertEqual(summary["outliers"], 2)
        self.assertAlmostEqual(summary["q1"], 0.46)
        self.assertAlmostEqual(summary["p90"], 0.684)
        self.assertAlmostEqual(summary["skewness"], 0.178488933752135)
        outliers = [analysis["value"] for analysis in entity["analyses"] if analysis["is_outlier"]]
        self.assertEqual(outliers, [0.2, 0.9])

    def test_repository_without_analysis(self):
        response = self.get("characteristic", "reliability", repository=self.web)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["period"], {"count": 0, "first": None, "last": None})
        self.assertEqual(data["entity"]["analyses"], [])
        self.assertEqual(data["entity"]["summary"]["count"], 0)
        self.assertIsNone(data["entity"]["summary"]["median"])
        self.assertEqual(data["children"], [])

    def test_invalid_level_is_rejected(self):
        self.assertEqual(self.get("file", "coverage").status_code, 400)

    def test_key_is_required_below_tsqmi(self):
        self.assertEqual(self.get("characteristic").status_code, 400)

    def test_entity_outside_release_configuration_is_rejected(self):
        self.assertEqual(self.get("subcharacteristic", "inexistente").status_code, 400)

    def test_repository_is_required(self):
        response = self.client.get(self.url, {"release_id": self.release.id, "level": "tsqmi"})

        self.assertEqual(response.status_code, 400)

    def test_release_is_required(self):
        response = self.client.get(self.url, {"repository_id": self.api.id, "level": "tsqmi"})

        self.assertEqual(response.status_code, 400)

    def test_repository_of_another_product_returns_404(self):
        other = self.get_repository(self.get_product(self.org, name="Outro"), name="x")

        self.assertEqual(self.get("tsqmi", repository=other).status_code, 404)

    def test_non_member_gets_404(self):
        outsider = get_user_model().objects.create(username="outsider", email="outsider@email.com")
        self.client.force_authenticate(outsider, token=Token.objects.create(user=outsider))

        self.assertEqual(self.get("tsqmi").status_code, 404)
