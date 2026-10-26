import copy
from datetime import datetime

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from resources import calculate_characteristics, calculate_subcharacteristics, calculate_tsqmi
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import CustomUser
from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from goals.models import Goal
from measures.models import CalculatedMeasure, SupportedMeasure
from release_configuration.models import ReleaseConfiguration
from releases.models import Release
from subcharacteristics.models import CalculatedSubCharacteristic, SupportedSubCharacteristic
from tsqmi.models import TSQMI
from utils.staticfiles import DEFAULT_PRE_CONFIG
from utils.tests import APITestCaseExpanded

MARCH = (2026, 3, 10)
FEBRUARY = (2026, 2, 10)


def local_datetime(*args):
    return timezone.make_aware(datetime(*args))


def core_tsqmi(measures, subcharacteristics, characteristics, weights=None):
    """
    TSQMI do default pre-config recalculado só com as funções do Core, para conferir a
    contribuição. `measures` são as de testing_status; o resto entra com o valor dado.
    """
    weights = weights or {"reliability": 34, "maintainability": 33, "functional_suitability": 33}
    testing_status = calculate_subcharacteristics(
        {
            "subcharacteristics": [
                {
                    "key": "testing_status",
                    "measures": [
                        {"key": key, "value": value, "weight": weight}
                        for key, value, weight in (
                            ("passed_tests", measures["passed_tests"], 33),
                            ("test_builds", measures["test_builds"], 33),
                            ("test_coverage", measures["test_coverage"], 34),
                        )
                    ],
                }
            ]
        }
    )["subcharacteristics"][0]["value"]
    reliability = calculate_characteristics(
        {
            "characteristics": [
                {
                    "key": "reliability",
                    "subcharacteristics": [
                        {"key": "testing_status", "value": testing_status, "weight": 50},
                        {"key": "maturity", "value": subcharacteristics["maturity"], "weight": 50},
                    ],
                }
            ]
        }
    )["characteristics"][0]["value"]
    values = {**characteristics, "reliability": reliability}
    return calculate_tsqmi(
        {
            "tsqmi": {
                "key": "tsqmi",
                "characteristics": [
                    {"key": key, "value": values[key], "weight": weight} for key, weight in weights.items()
                ],
            }
        }
    )["tsqmi"][0]["value"]


class EntityMatrixEndpointTestCase(APITestCaseExpanded):
    def setUp(self):
        self.client = APIClient()
        self.user = self.get_or_create_test_user()
        self.client.force_authenticate(self.user, token=Token.objects.create(user=self.user))

        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.api = self.get_repository(self.product, name="api")
        self.web = self.get_repository(self.product, name="web")

        self.goal = Goal.objects.create(created_by=self.user, product=self.product, data={"reliability": 70})
        self.previous_release = self.release_between("R1", (2026, 2, 1), (2026, 2, 28))
        self.release = self.release_between("R2", (2026, 3, 1), (2026, 3, 31))
        self.url = f"/api/v1/organizations/{self.org.id}/products/{self.product.id}/entity-analysis/matrix/"

    def release_between(self, name, start, end):
        return Release.objects.create(
            release_name=name,
            start_at=local_datetime(*start),
            end_at=local_datetime(*end),
            created_by=self.user,
            product=self.product,
            goal=self.goal,
        )

    def get(self, level, release=None, client=None):
        return (client or self.client).get(self.url, {"release_id": (release or self.release).id, "level": level})

    def save_values(self, repository, when, measures=(), subcharacteristics=(), characteristics=(), tsqmi=None):
        created_at = local_datetime(*when)
        for key, value in dict(measures).items():
            CalculatedMeasure.objects.create(
                measure=SupportedMeasure.objects.get(key=key),
                repository=repository,
                value=value,
                created_at=created_at,
            )
        for key, value in dict(subcharacteristics).items():
            CalculatedSubCharacteristic.objects.create(
                subcharacteristic=SupportedSubCharacteristic.objects.get(key=key),
                repository=repository,
                value=value,
                created_at=created_at,
            )
        for key, value in dict(characteristics).items():
            CalculatedCharacteristic.objects.create(
                characteristic=SupportedCharacteristic.objects.get(key=key),
                repository=repository,
                value=value,
                created_at=created_at,
            )
        if tsqmi is not None:
            TSQMI.objects.create(repository=repository, value=tsqmi, created_at=created_at)

    def save_api_release_values(self):
        self.march_measures = {"passed_tests": 0.9, "test_builds": 0.8, "test_coverage": 0.5}
        self.march_subcharacteristics = {"testing_status": 0.74, "maturity": 0.7, "modifiability": 0.6}
        self.march_characteristics = {"reliability": 0.72, "maintainability": 0.6, "functional_suitability": 0.5}
        self.save_values(
            self.api,
            MARCH,
            measures=self.march_measures,
            subcharacteristics=self.march_subcharacteristics,
            characteristics=self.march_characteristics,
            tsqmi=0.61,
        )
        self.save_values(
            self.api,
            FEBRUARY,
            measures={"passed_tests": 0.9, "test_coverage": 0.8},
            characteristics={"reliability": 0.8},
            tsqmi=0.66,
        )

    def cells(self, response, repository="api"):
        row = next(row for row in response.json()["repositories"] if row["name"] == repository)
        return {cell["key"]: cell for cell in row["cells"]}

    def test_characteristic_columns_follow_release_configuration_with_weight(self):
        response = self.get("characteristic")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["level"], "characteristic")
        self.assertEqual(
            data["columns"],
            [
                {"key": "reliability", "name": "Reliability", "weight": 34, "path": []},
                {"key": "maintainability", "name": "Maintainability", "weight": 33, "path": []},
                {"key": "functional_suitability", "name": "Functional Suitability", "weight": 33, "path": []},
            ],
        )

    def test_measure_columns_carry_the_path_up_to_the_characteristic(self):
        columns = {column["key"]: column for column in self.get("measure").json()["columns"]}

        self.assertEqual(list(columns)[:3], ["passed_tests", "test_builds", "test_coverage"])
        self.assertEqual(columns["test_coverage"]["weight"], 34)
        self.assertEqual(
            columns["test_coverage"]["path"],
            [
                {"level": "characteristic", "key": "reliability", "name": "Reliability", "weight": 34},
                {"level": "subcharacteristic", "key": "testing_status", "name": "Testing Status", "weight": 50},
            ],
        )

    def test_rows_bring_release_and_previous_release_values(self):
        self.save_api_release_values()

        data = self.get("measure").json()

        self.assertEqual(data["previous_release"]["id"], self.previous_release.id)
        api = next(row for row in data["repositories"] if row["name"] == "api")
        self.assertEqual(api["tsqmi"], {"value": 0.61, "previous_value": 0.66})
        cells = self.cells(self.get("measure"))
        self.assertEqual(cells["test_coverage"]["value"], 0.5)
        self.assertEqual(cells["test_coverage"]["previous_value"], 0.8)
        # sem valor na release anterior
        self.assertIsNone(cells["test_builds"]["previous_value"])
        self.assertIsNone(cells["test_builds"]["contribution"])

    def test_repository_without_value_has_null_cells(self):
        self.save_api_release_values()

        web = next(row for row in self.get("measure").json()["repositories"] if row["name"] == "web")

        self.assertEqual(web["tsqmi"], {"value": None, "previous_value": None})
        self.assertTrue(all(cell["value"] is None and cell["contribution"] is None for cell in web["cells"]))

    def test_contribution_matches_core_recalculation_of_tsqmi(self):
        self.save_api_release_values()

        cells = self.cells(self.get("measure"))

        expected = core_tsqmi(
            self.march_measures, self.march_subcharacteristics, self.march_characteristics
        ) - core_tsqmi(
            {**self.march_measures, "test_coverage": 0.8}, self.march_subcharacteristics, self.march_characteristics
        )
        self.assertLess(expected, 0)
        self.assertAlmostEqual(cells["test_coverage"]["contribution"], expected)
        # entidade que não mudou não puxa o TSQMI
        self.assertAlmostEqual(cells["passed_tests"]["contribution"], 0)

    def test_characteristic_contribution_recalculates_only_the_tsqmi(self):
        self.save_api_release_values()

        cells = self.cells(self.get("characteristic"))

        weights = [34, 33, 33]
        current = calculate_tsqmi(
            {
                "tsqmi": {
                    "key": "tsqmi",
                    "characteristics": [
                        {"key": key, "value": value, "weight": weight}
                        for (key, value), weight in zip(self.march_characteristics.items(), weights)
                    ],
                }
            }
        )["tsqmi"][0]["value"]
        previous = calculate_tsqmi(
            {
                "tsqmi": {
                    "key": "tsqmi",
                    "characteristics": [
                        {"key": key, "value": value, "weight": weight}
                        for (key, value), weight in zip(
                            {**self.march_characteristics, "reliability": 0.8}.items(), weights
                        )
                    ],
                }
            }
        )["tsqmi"][0]["value"]
        self.assertAlmostEqual(cells["reliability"]["contribution"], current - previous)

    def test_first_release_has_no_previous_release(self):
        self.save_api_release_values()

        response = self.get("measure", release=self.previous_release)

        self.assertIsNone(response.json()["previous_release"])
        cells = self.cells(response)
        self.assertEqual(cells["test_coverage"]["value"], 0.8)
        self.assertIsNone(cells["test_coverage"]["previous_value"])
        self.assertIsNone(cells["test_coverage"]["contribution"])

    def test_previous_release_is_the_one_right_before_by_start_at(self):
        # criada por último, mas começa antes da R1
        self.release_between("R0", (2026, 1, 1), (2026, 1, 31))

        self.assertEqual(self.get("measure").json()["previous_release"]["id"], self.previous_release.id)

    def test_contribution_uses_weights_of_the_chosen_release_configuration(self):
        data = copy.deepcopy(DEFAULT_PRE_CONFIG)
        data["characteristics"] = [c for c in data["characteristics"] if c["key"] != "functional_suitability"]
        data["characteristics"][0]["weight"] = 80
        data["characteristics"][1]["weight"] = 20
        # vigente só na R2: a R1 continua com a configuração padrão
        ReleaseConfiguration.objects.create(
            product=self.product, name="Sem functional_suitability", data=data, created_at=local_datetime(2026, 3, 5)
        )
        ReleaseConfiguration.objects.create(
            product=self.product, name="Padrão", data=DEFAULT_PRE_CONFIG, created_at=local_datetime(2026, 1, 1)
        )
        self.save_api_release_values()

        response = self.get("measure")

        self.assertNotIn("team_throughput", [column["key"] for column in response.json()["columns"]])
        self.assertEqual(response.json()["columns"][0]["path"][0]["weight"], 80)
        weights = {"reliability": 80, "maintainability": 20}
        expected = core_tsqmi(
            self.march_measures, self.march_subcharacteristics, self.march_characteristics, weights
        ) - core_tsqmi(
            {**self.march_measures, "test_coverage": 0.8},
            self.march_subcharacteristics,
            self.march_characteristics,
            weights,
        )
        self.assertAlmostEqual(self.cells(response)["test_coverage"]["contribution"], expected)
        # na R1, a configuração padrão
        previous_columns = self.get("characteristic", release=self.previous_release).json()["columns"]
        self.assertIn("functional_suitability", [column["key"] for column in previous_columns])

    def test_query_count_does_not_grow_with_repositories(self):
        self.save_api_release_values()

        def count_queries():
            with CaptureQueriesContext(connection) as context:
                self.assertEqual(self.get("measure").status_code, 200)
            return len(context)

        before = count_queries()
        for index in range(4):
            repository = self.get_repository(self.product, name=f"extra-{index}")
            self.save_values(repository, MARCH, measures=self.march_measures, tsqmi=0.5)
        self.assertEqual(count_queries(), before)

    def test_does_not_leak_repository_of_another_product_linked_to_the_release(self):
        other_org = self.get_organization(name="Other Organization", add_user=False)
        foreign = self.get_repository(self.get_product(other_org, name="Other Product"), name="foreign")
        self.release.repositories.add(self.api, foreign)

        names = [row["name"] for row in self.get("characteristic").json()["repositories"]]

        self.assertEqual(names, ["api"])

    def test_invalid_parameters_return_400(self):
        for params in (
            {"release_id": self.release.id},
            {"release_id": self.release.id, "level": "metric"},
            {"level": "measure"},
        ):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(self.url, params).status_code, 400)

    def test_user_who_is_not_member_cannot_access(self):
        outsider = CustomUser.objects.create(username="outsider", email="outsider@example.com")
        client = APIClient()
        client.force_authenticate(outsider, token=Token.objects.create(user=outsider))

        self.assertEqual(self.get("measure", client=client).status_code, 404)

    def test_unauthenticated_user_cannot_access(self):
        self.assertEqual(self.get("measure", client=APIClient()).status_code, 401)
