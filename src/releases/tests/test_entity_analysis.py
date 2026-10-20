from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

import copy

from accounts.models import CustomUser
from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from goals.models import Goal
from measures.models import CalculatedMeasure, SupportedMeasure
from metrics.models import CollectedMetric, SupportedMetric
from release_configuration.models import ReleaseConfiguration
from releases.models import Release
from subcharacteristics.models import CalculatedSubCharacteristic, SupportedSubCharacteristic
from utils.staticfiles import DEFAULT_PRE_CONFIG
from utils.tests import APITestCaseExpanded


def local_datetime(*args):
    return timezone.make_aware(datetime(*args))


class EntityAnalysisEndpointTestCase(APITestCaseExpanded):
    def setUp(self):
        self.client = APIClient()
        self.user = self.get_or_create_test_user()
        self.client.force_authenticate(self.user, token=Token.objects.create(user=self.user))

        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.api = self.get_repository(self.product, name="api")
        self.parser = self.get_repository(self.product, name="parser")
        self.web = self.get_repository(self.product, name="web")

        self.goal = Goal.objects.create(
            created_by=self.user,
            product=self.product,
            data={"reliability": 70, "maintainability": 60},
        )
        self.release = Release.objects.create(
            release_name="v1.0",
            start_at=local_datetime(2026, 3, 1),
            end_at=local_datetime(2026, 3, 31),
            created_by=self.user,
            product=self.product,
            goal=self.goal,
        )
        self.url = f"/api/v1/organizations/{self.org.id}/products/{self.product.id}/entity-analysis/"

    def get(self, level, key, release=None, url=None):
        release = release or self.release
        return self.client.get(url or self.url, {"release_id": release.id, "level": level, "key": key})

    def calculated_characteristic(self, repository, key, value, created_at):
        return CalculatedCharacteristic.objects.create(
            characteristic=SupportedCharacteristic.objects.get(key=key),
            repository=repository,
            value=value,
            created_at=created_at,
        )

    def calculated_subcharacteristic(self, repository, key, value, created_at):
        return CalculatedSubCharacteristic.objects.create(
            subcharacteristic=SupportedSubCharacteristic.objects.get(key=key),
            repository=repository,
            value=value,
            created_at=created_at,
        )

    def calculated_measure(self, repository, key, value, created_at):
        return CalculatedMeasure.objects.create(
            measure=SupportedMeasure.objects.get(key=key),
            repository=repository,
            value=value,
            created_at=created_at,
        )

    def collected_metric(self, repository, key, value, created_at, qualifier="TRK", path=None):
        return CollectedMetric.objects.create(
            metric=SupportedMetric.objects.get(key=key),
            repository=repository,
            value=value,
            created_at=created_at,
            qualifier=qualifier,
            path=path,
        )

    def repositories_by_name(self, response):
        return {repository["name"]: repository for repository in response.json()["repositories"]}

    def test_characteristic_uses_latest_value_inside_release_window(self):
        self.calculated_characteristic(self.api, "maintainability", 0.4, local_datetime(2026, 3, 5))
        self.calculated_characteristic(self.api, "maintainability", 0.8, local_datetime(2026, 3, 20))
        # fora da janela: antes e depois da release
        self.calculated_characteristic(self.api, "maintainability", 0.1, local_datetime(2026, 2, 27))
        self.calculated_characteristic(self.api, "maintainability", 0.9, local_datetime(2026, 4, 2))
        self.calculated_characteristic(self.parser, "maintainability", 0.3, local_datetime(2026, 3, 10))

        response = self.get("characteristic", "maintainability")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["level"], "characteristic")
        self.assertEqual(data["entity"]["key"], "maintainability")
        self.assertEqual(data["release"]["id"], self.release.id)

        repositories = self.repositories_by_name(response)
        self.assertEqual(list(repositories), ["api", "parser", "web"])
        self.assertEqual(repositories["api"]["value"], 0.8)
        self.assertEqual(repositories["parser"]["value"], 0.3)

    def test_repository_without_value_in_release_is_null(self):
        self.calculated_characteristic(self.api, "maintainability", 0.8, local_datetime(2026, 3, 20))

        repositories = self.repositories_by_name(self.get("characteristic", "maintainability"))

        self.assertIsNone(repositories["web"]["value"])
        self.assertIsNone(repositories["web"]["created_at"])

    def test_last_day_of_release_is_inside_the_window(self):
        self.calculated_characteristic(self.api, "maintainability", 0.75, local_datetime(2026, 3, 31, 18, 30))

        repositories = self.repositories_by_name(self.get("characteristic", "maintainability"))

        self.assertEqual(repositories["api"]["value"], 0.75)

    def test_characteristic_reference_is_release_goal(self):
        response = self.get("characteristic", "reliability")

        self.assertEqual(response.json()["reference"], {"goal": 0.7})

    def test_characteristic_children_are_subcharacteristics_with_weight_and_value(self):
        self.calculated_subcharacteristic(self.parser, "modifiability", 0.45, local_datetime(2026, 3, 12))

        repositories = self.repositories_by_name(self.get("characteristic", "maintainability"))

        children = {child["key"]: child for child in repositories["parser"]["children"]}
        self.assertEqual(children["modifiability"]["weight"], 100)
        self.assertEqual(children["modifiability"]["value"], 0.45)
        self.assertIsNone(repositories["api"]["children"][0]["value"])

    def test_subcharacteristic_children_are_measures(self):
        self.calculated_subcharacteristic(self.api, "testing_status", 0.6, local_datetime(2026, 3, 12))
        self.calculated_measure(self.api, "test_coverage", 0.5, local_datetime(2026, 3, 12))

        response = self.get("subcharacteristic", "testing_status")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["reference"])
        api = self.repositories_by_name(response)["api"]
        self.assertEqual(api["value"], 0.6)
        children = {child["key"]: child for child in api["children"]}
        self.assertEqual(set(children), {"passed_tests", "test_builds", "test_coverage"})
        self.assertEqual(children["test_coverage"]["weight"], 34)
        self.assertEqual(children["test_coverage"]["value"], 0.5)

    def test_measure_reference_is_threshold_range_and_children_are_metrics(self):
        self.calculated_measure(self.web, "test_coverage", 0.25, local_datetime(2026, 3, 15))
        self.collected_metric(self.web, "coverage", 72.5, local_datetime(2026, 3, 15))

        response = self.get("measure", "test_coverage")

        data = response.json()
        self.assertEqual(data["reference"], {"min_threshold": 60, "max_threshold": 100})
        web = self.repositories_by_name(response)["web"]
        self.assertEqual(web["value"], 0.25)
        self.assertEqual(
            [(child["key"], child["weight"], child["value"]) for child in web["children"]],
            [("coverage", None, 72.5)],
        )

    def test_metric_returns_project_level_raw_value(self):
        self.collected_metric(self.api, "coverage", 81.0, local_datetime(2026, 3, 15))
        # valor de arquivo não é o valor do repositório
        self.collected_metric(self.api, "coverage", 10.0, local_datetime(2026, 3, 16), qualifier="FIL", path="a.py")
        self.collected_metric(self.parser, "coverage", 5.0, local_datetime(2026, 3, 16), qualifier="FIL", path="b.py")

        response = self.get("metric", "coverage")

        data = response.json()
        self.assertEqual(data["entity"]["metric_type"], "FLOAT")
        self.assertIsNone(data["reference"])
        repositories = self.repositories_by_name(response)
        self.assertEqual(repositories["api"]["value"], 81.0)
        self.assertIsNone(repositories["parser"]["value"])
        self.assertEqual(repositories["api"]["children"], [])

    def test_release_without_analysis_returns_every_repository_without_value(self):
        self.calculated_characteristic(self.api, "maintainability", 0.8, local_datetime(2026, 5, 1))

        response = self.get("characteristic", "maintainability")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(repository["value"] is None for repository in response.json()["repositories"]))

    def test_uses_only_release_repositories_when_release_has_them(self):
        self.release.repositories.set([self.api, self.web])

        repositories = self.repositories_by_name(self.get("characteristic", "maintainability"))

        self.assertEqual(list(repositories), ["api", "web"])

    def test_entity_outside_release_configuration_returns_404(self):
        response = self.get("characteristic", "security")

        self.assertEqual(response.status_code, 404)

    def test_invalid_parameters_return_400(self):
        cases = [
            {"release_id": self.release.id, "level": "tsqmi", "key": "maintainability"},
            {"release_id": self.release.id, "level": "characteristic"},
            {"level": "characteristic", "key": "maintainability"},
            {"release_id": "abc", "level": "characteristic", "key": "maintainability"},
        ]

        for params in cases:
            with self.subTest(params=params):
                self.assertEqual(self.client.get(self.url, params).status_code, 400)

    def test_release_of_another_product_returns_404(self):
        other_product = self.get_product(self.org, name="Other Product")
        other_release = Release.objects.create(
            release_name="v9",
            start_at=local_datetime(2026, 3, 1),
            end_at=local_datetime(2026, 3, 31),
            created_by=self.user,
            product=other_product,
            goal=self.goal,
        )

        response = self.get("characteristic", "maintainability", release=other_release)

        self.assertEqual(response.status_code, 404)

    def test_user_who_is_not_member_cannot_access(self):
        outsider = CustomUser.objects.create(username="outsider", email="outsider@example.com")
        client = APIClient()
        client.force_authenticate(outsider, token=Token.objects.create(user=outsider))

        response = client.get(
            self.url, {"release_id": self.release.id, "level": "characteristic", "key": "reliability"}
        )

        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_cannot_access(self):
        response = APIClient().get(
            self.url, {"release_id": self.release.id, "level": "characteristic", "key": "reliability"}
        )

        self.assertEqual(response.status_code, 401)

    def test_entities_lists_release_configuration_by_level(self):
        response = self.client.get(f"{self.url}entities/", {"release_id": self.release.id})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(set(data), {"characteristic", "subcharacteristic", "measure", "metric"})
        self.assertEqual(
            [item["key"] for item in data["characteristic"]],
            ["reliability", "maintainability", "functional_suitability"],
        )
        self.assertIn({"key": "test_coverage", "name": "Test Coverage"}, data["measure"])
        self.assertIn("coverage", [item["key"] for item in data["metric"]])

    def test_entities_requires_release(self):
        response = self.client.get(f"{self.url}entities/")

        self.assertEqual(response.status_code, 400)

    def configuration_without_functional_suitability(self, created_at):
        data = copy.deepcopy(DEFAULT_PRE_CONFIG)
        data["characteristics"] = [c for c in data["characteristics"] if c["key"] != "functional_suitability"]
        data["characteristics"][0]["weight"] = 50
        data["characteristics"][1]["weight"] = 50
        return ReleaseConfiguration.objects.create(
            product=self.product,
            name="Configuração sem functional_suitability",
            data=data,
            created_at=created_at,
        )

    def characteristic_keys_of_release(self):
        entities = self.client.get(f"{self.url}entities/", {"release_id": self.release.id}).json()
        return [item["key"] for item in entities["characteristic"]]

    def test_uses_latest_configuration_created_until_release_end(self):
        # a configuração padrão do produto foi criada agora, depois da release
        self.configuration_without_functional_suitability(local_datetime(2026, 3, 20))

        self.assertEqual(self.characteristic_keys_of_release(), ["reliability", "maintainability"])
        self.assertEqual(self.get("characteristic", "functional_suitability").status_code, 404)

    def test_falls_back_to_oldest_configuration_when_none_existed_until_release_end(self):
        # as duas configurações são posteriores à release: vale a mais antiga, a padrão criada com o produto
        self.configuration_without_functional_suitability(timezone.now() + timedelta(days=1))

        self.assertIn("functional_suitability", self.characteristic_keys_of_release())
