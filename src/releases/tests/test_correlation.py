from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from goals.models import Goal
from releases.correlation import critical_value
from releases.models import Release
from subcharacteristics.models import CalculatedSubCharacteristic, SupportedSubCharacteristic
from utils.tests import APITestCaseExpanded


def local_datetime(*args):
    return timezone.make_aware(datetime(*args))


# Colunas C1, C3 e C6 do Exemplo 7 do modelo matemático da correlação, uma release por linha, como
# reliability, maintainability e functional_suitability. No documento, RD_Corr (Spearman):
# C1 × C3 = 0,56, C1 × C6 = 0,49 e C3 × C6 = 0,93.
EXAMPLE_7_KEYS = ["reliability", "maintainability", "functional_suitability"]
EXAMPLE_7_RD = [
    [0.63, 0.63, 0.45],
    [0.63, 0.63, 0.45],
    [0.63, 0.45, 0.45],
    [0.63, 0.45, 0.45],
    [0.63, 0.45, 0.45],
    [0.85, 0.63, 0.45],
    [0.85, 0.63, 0.45],
    [0.85, 0.63, 0.45],
    [0.65, 0.65, 0.51],
    [0.65, 0.65, 0.51],
    [0.69, 0.69, 0.65],
    [0.69, 0.69, 0.65],
    [0.69, 0.69, 0.65],
    [0.69, 0.69, 0.65],
    [0.69, 0.69, 0.65],
    [0.69, 0.69, 0.65],
    [0.63, 0.63, 0.45],
    [0.63, 0.63, 0.45],
    [0.63, 0.63, 0.45],
    [0.63, 0.63, 0.45],
]


class CriticalValueTestCase(SimpleTestCase):
    def test_critical_value_with_20_releases(self):
        # nota da tela de referência: não significativo com |r| < 0,44 (p < 0,05, n = 20)
        self.assertAlmostEqual(critical_value(20), 0.4438, places=4)

    def test_critical_value_decreases_with_more_releases(self):
        self.assertGreater(critical_value(3), critical_value(10))


class CorrelationEndpointTestCase(APITestCaseExpanded):
    def setUp(self):
        self.client = APIClient()
        self.user = self.get_or_create_test_user()
        self.client.force_authenticate(self.user, token=Token.objects.create(user=self.user))

        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.api = self.get_repository(self.product, name="api")
        self.goal = Goal.objects.create(created_by=self.user, product=self.product, data={"reliability": 70})
        self.url = f"/api/v1/organizations/{self.org.id}/products/{self.product.id}/correlation/"

    def get(self, level=None, repository=None):
        query = {"repository_id": (repository or self.api).id}
        if level is not None:
            query["level"] = level
        return self.client.get(self.url, query)

    def create_releases(self, count):
        """Releases semanais a partir de 05/01/2026, da mais antiga para a mais nova."""
        start = local_datetime(2026, 1, 5)
        return [
            Release.objects.create(
                release_name=f"R{index + 1}",
                start_at=start + timedelta(weeks=index),
                end_at=start + timedelta(weeks=index, days=6),
                created_by=self.user,
                product=self.product,
                goal=self.goal,
            )
            for index in range(count)
        ]

    def characteristic(self, key, value, in_release, hours=10, **fields):
        return CalculatedCharacteristic.objects.create(
            characteristic=SupportedCharacteristic.objects.get(key=key),
            repository=self.api,
            value=value,
            created_at=in_release.start_at + timedelta(hours=hours),
            **fields,
        )

    def subcharacteristic(self, key, value, release):
        return CalculatedSubCharacteristic.objects.create(
            subcharacteristic=SupportedSubCharacteristic.objects.get(key=key),
            repository=self.api,
            value=value,
            created_at=release.start_at + timedelta(hours=10),
        )

    def characteristics(self, releases, values):
        for key, series in values.items():
            for release, value in zip(releases, series):
                self.characteristic(key, value, release)

    def pairs(self, data):
        return {(pair["row"], pair["column"]): pair for pair in data["pairs"]}

    def test_example_7_applies_spearman_and_matches_the_document(self):
        releases = self.create_releases(20)
        self.characteristics(releases, dict(zip(EXAMPLE_7_KEYS, zip(*EXAMPLE_7_RD))))

        response = self.get("characteristic")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["repository"], {"id": self.api.id, "name": "api"})
        self.assertEqual(data["level"], "characteristic")
        self.assertEqual(
            [entity["key"] for entity in data["entities"]],
            ["reliability", "maintainability", "functional_suitability"],
        )
        self.assertEqual([release["id"] for release in data["releases"]], [release.id for release in releases])
        self.assertEqual(data["excluded_releases"], 0)
        self.assertEqual(data["method"], "spearman")
        self.assertEqual(data["non_normal"], 3)
        self.assertAlmostEqual(data["critical_value"], 0.4438, places=4)
        self.assertIsNone(data["reason"])

        pairs = self.pairs(data)
        self.assertEqual(
            list(pairs),
            [
                ("maintainability", "reliability"),
                ("functional_suitability", "reliability"),
                ("functional_suitability", "maintainability"),
            ],
        )
        self.assertEqual(round(pairs[("maintainability", "reliability")]["coefficient"], 2), 0.56)
        self.assertEqual(round(pairs[("functional_suitability", "reliability")]["coefficient"], 2), 0.49)
        self.assertEqual(round(pairs[("functional_suitability", "maintainability")]["coefficient"], 2), 0.93)
        for pair in pairs.values():
            self.assertLess(pair["p_value"], 0.05)
            self.assertTrue(pair["significant"])

    def test_level_defaults_to_characteristic(self):
        self.assertEqual(self.get().json()["level"], "characteristic")

    def test_subcharacteristic_level(self):
        releases = self.create_releases(3)
        values = {
            "testing_status": [0.2, 0.5, 0.8],
            "maturity": [0.3, 0.4, 0.8],
            "modifiability": [0.8, 0.5, 0.2],
            "functional_completeness": [0.5, 0.7, 0.6],
        }
        for key, series in values.items():
            for release, value in zip(releases, series):
                self.subcharacteristic(key, value, release)

        data = self.get("subcharacteristic").json()

        self.assertEqual(
            [entity["key"] for entity in data["entities"]],
            ["testing_status", "maturity", "modifiability", "functional_completeness"],
        )
        self.assertEqual(len(data["releases"]), 3)
        self.assertEqual(len(data["pairs"]), 6)
        self.assertAlmostEqual(self.pairs(data)[("modifiability", "testing_status")]["coefficient"], -1)

    def test_uses_the_latest_analysis_of_each_release(self):
        releases = self.create_releases(3)
        self.characteristics(releases, {"reliability": [0.1, 0.2, 0.3], "maintainability": [0.3, 0.2, 0.1]})
        self.characteristic("functional_suitability", 0.5, releases[0])
        self.characteristic("functional_suitability", 0.6, releases[1])
        self.characteristic("functional_suitability", 0.7, releases[2])
        # análise mais recente da primeira release
        self.characteristic("functional_suitability", 0.9, releases[0], hours=20)

        data = self.get().json()

        # com 3 releases as colunas são normais: Pearson de 0,9 / 0,6 / 0,7 contra 0,1 / 0,2 / 0,3
        self.assertEqual(data["method"], "pearson")
        self.assertAlmostEqual(self.pairs(data)[("functional_suitability", "reliability")]["coefficient"], -0.6547, 4)

    def test_release_without_value_of_an_entity_is_excluded(self):
        releases = self.create_releases(4)
        self.characteristics(
            releases,
            {"reliability": [0.1, 0.2, 0.3, 0.4], "maintainability": [0.4, 0.3, 0.2, 0.1]},
        )
        self.characteristics(
            [releases[0], releases[1], releases[3]],
            {"functional_suitability": [0.5, 0.6, 0.7]},
        )

        data = self.get().json()

        self.assertEqual(
            [release["id"] for release in data["releases"]], [releases[0].id, releases[1].id, releases[3].id]
        )
        self.assertEqual(data["excluded_releases"], 1)
        self.assertEqual(len(data["pairs"]), 3)

    def test_release_closing_rows_are_not_analyses(self):
        releases = self.create_releases(3)
        self.characteristics(
            releases,
            {
                "reliability": [0.1, 0.2, 0.3],
                "maintainability": [0.4, 0.3, 0.2],
                "functional_suitability": [0.5, 0.9, 0.7],
            },
        )
        # linha do fechamento, mais recente, na janela da terceira release
        self.characteristic("functional_suitability", 0.1, releases[2], hours=150, release=releases[2])

        pairs = self.pairs(self.get().json())

        # com a linha do fechamento, functional_suitability seria 0,5 / 0,9 / 0,1 e o coeficiente, −0,5
        self.assertAlmostEqual(pairs[("functional_suitability", "reliability")]["coefficient"], 0.5)

    def test_less_than_3_releases_has_no_pairs(self):
        releases = self.create_releases(2)
        self.characteristics(
            releases,
            {"reliability": [0.1, 0.2], "maintainability": [0.4, 0.3], "functional_suitability": [0.5, 0.6]},
        )

        data = self.get().json()

        self.assertEqual(data["reason"], "insufficient_releases")
        self.assertEqual(data["pairs"], [])
        self.assertEqual(len(data["releases"]), 2)
        self.assertIsNone(data["method"])
        self.assertIsNone(data["critical_value"])

    def test_repository_without_analysis(self):
        self.create_releases(3)

        data = self.get().json()

        self.assertEqual(data["reason"], "insufficient_releases")
        self.assertEqual(data["releases"], [])
        self.assertEqual(data["excluded_releases"], 3)

    def test_product_without_release(self):
        data = self.get().json()

        self.assertEqual(data["reason"], "insufficient_entities")
        self.assertEqual(data["entities"], [])
        self.assertEqual(data["releases"], [])

    def test_constant_entity_has_no_coefficient(self):
        releases = self.create_releases(3)
        self.characteristics(
            releases,
            {
                "reliability": [0.1, 0.2, 0.3],
                "maintainability": [0.5, 0.5, 0.5],
                "functional_suitability": [0.3, 0.1, 0.2],
            },
        )

        data = self.get().json()
        pairs = self.pairs(data)

        self.assertEqual(data["method"], "spearman")
        for pair in (("maintainability", "reliability"), ("functional_suitability", "maintainability")):
            self.assertIsNone(pairs[pair]["coefficient"])
            self.assertIsNone(pairs[pair]["p_value"])
            self.assertFalse(pairs[pair]["significant"])
        self.assertIsNotNone(pairs[("functional_suitability", "reliability")]["coefficient"])

    def test_invalid_level_is_rejected(self):
        self.assertEqual(self.get("measure").status_code, 400)

    def test_repository_is_required(self):
        self.assertEqual(self.client.get(self.url, {"level": "characteristic"}).status_code, 400)

    def test_repository_of_another_product_returns_404(self):
        other = self.get_repository(self.get_product(self.org, name="Outro"), name="x")

        self.assertEqual(self.get(repository=other).status_code, 404)

    def test_non_member_gets_404(self):
        outsider = get_user_model().objects.create(username="outsider", email="outsider@email.com")
        self.client.force_authenticate(outsider, token=Token.objects.create(user=outsider))

        self.assertEqual(self.get().status_code, 404)
