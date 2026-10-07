import json
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model

from characteristics.models import CalculatedCharacteristic
from measures.models import CalculatedMeasure
from subcharacteristics.models import CalculatedSubCharacteristic
from tsqmi.models import TSQMI
from utils.tests import APITestCaseExpanded


REFERENCE = Path(__file__).parent / "data" / "cli_service_parity"
FIXTURE = REFERENCE / "github-extracted.metrics"


class TestCliServiceParity(APITestCaseExpanded):
    def test_same_github_metrics_and_configuration(self):
        expected = json.loads(
            (REFERENCE / "calc_msgram.json").read_text()
        )
        assert len(expected) == 1
        expected = expected[0]

        config = json.loads(
            (REFERENCE / "msgram.json").read_text()
        )
        extracted = json.loads(FIXTURE.read_text())
        assert len(extracted) == 1
        metrics = next(iter(extracted.values()))

        self.user = get_user_model().objects.create_user(
            username="task50-parity", password="test-only"
        )
        self.client.force_authenticate(user=self.user)
        org = self.get_organization()
        product = self.get_product(org)
        repository = self.get_repository(product)

        # Todas as configurações deste produto de teste usam
        # exatamente o mesmo conteúdo fornecido à CLI.
        release_config = product.release_configuration.first()
        assert release_config is not None
        assert release_config.data == config, (
            "A configuração padrão do Service difere da configuração da CLI",
            release_config.data,
            config,
        )

        payload = {
            "github": {
                "metrics": [
                    {"name": item["metric"], "value": item["value"]}
                    for item in metrics
                ]
            }
        }
        url = (
            f"/api/v1/organizations/{org.id}"
            f"/products/{product.id}"
            f"/repositories/{repository.id}"
            "/calculate/math-model/"
        )

        response = self.client.post(url, payload, format="json")
        assert response.status_code == 201, (
            response.status_code, response.content.decode()
        )

        actual = {}
        for section, model, key_field in [
            ("measures", CalculatedMeasure, "measure__key"),
            (
                "subcharacteristics",
                CalculatedSubCharacteristic,
                "subcharacteristic__key",
            ),
            (
                "characteristics",
                CalculatedCharacteristic,
                "characteristic__key",
            ),
        ]:
            actual[section] = dict(
                model.objects.filter(repository=repository)
                .values_list(key_field, "value")
            )

        actual["tsqmi"] = {
            "tsqmi": TSQMI.objects.get(repository=repository).value
        }

        print("\nResultado Service:", json.dumps(actual, indent=2))
        for section, values in actual.items():
            cli_values = {
                item["key"]: item["value"]
                for item in expected[section]
            }
            assert values.keys() == cli_values.keys(), (
                section, "Chaves diferentes", values, cli_values
            )
            for key, value in values.items():
                assert value == pytest.approx(
                    cli_values[key], rel=1e-9, abs=1e-12
                ), (section, key, value, cli_values[key])


class TestMissingMetrics(APITestCaseExpanded):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="task50-missing", password="test-only"
        )
        self.client.force_authenticate(user=self.user)
        org = self.get_organization()
        product = self.get_product(org)
        self.repository = self.get_repository(product)
        self.url = (
            f"/api/v1/organizations/{org.id}"
            f"/products/{product.id}"
            f"/repositories/{self.repository.id}"
            "/calculate/math-model/"
        )

    def post_metrics(self, metrics):
        return self.client.post(
            self.url,
            {
                "github": {
                    "metrics": [
                        {"name": key, "value": value}
                        for key, value in metrics.items()
                    ]
                }
            },
            format="json",
        )

    def calculated_measures(self):
        return dict(
            CalculatedMeasure.objects.filter(repository=self.repository)
            .values_list("measure__key", "value")
        )

    def test_zero_builds_is_valid_and_neutral(self):
        response = self.post_metrics({
            "sum_ci_feedback_times": 0,
            "total_builds": 0,
        })
        assert response.status_code == 201, response.content
        measures = self.calculated_measures()
        assert set(measures) == {"ci_feedback_time"}
        assert measures["ci_feedback_time"] == pytest.approx(0.5)

    def test_missing_build_count_omits_feedback_measure(self):
        response = self.post_metrics({
            "sum_ci_feedback_times": 925,
            "resolved_issues": 1,
            "total_issues": 6,
        })
        assert response.status_code == 201, response.content
        measures = self.calculated_measures()
        assert set(measures) == {"team_throughput"}
        assert measures["team_throughput"] == pytest.approx(0.0)
        assert not CalculatedCharacteristic.objects.filter(
            repository=self.repository,
            characteristic__key="reliability",
        ).exists()

    def test_empty_payload_returns_400_without_persistence(self):
        from metrics.models import CollectedMetric

        models = (
            CollectedMetric,
            CalculatedMeasure,
            CalculatedSubCharacteristic,
            CalculatedCharacteristic,
            TSQMI,
        )
        before = {
            model: model.objects.filter(repository=self.repository).count()
            for model in models
        }

        response = self.client.post(self.url, {}, format="json")
        assert response.status_code == 400, response.content

        for model in models:
            assert (
                model.objects.filter(repository=self.repository).count()
                == before[model]
            )


class TestFullCliServiceParity(APITestCaseExpanded):
    def test_same_full_metrics_and_configuration(self):
        expected = json.loads(
            (REFERENCE / "full" / "calc_msgram.json").read_text()
        )
        assert len(expected) == 1
        expected = expected[0]

        config = json.loads(
            (REFERENCE / "full" / "msgram.json").read_text()
        )
        self.user = get_user_model().objects.create_user(
            username="task50-parity", password="test-only"
        )
        self.client.force_authenticate(user=self.user)
        org = self.get_organization()
        product = self.get_product(org)
        repository = self.get_repository(product)

        # Todas as configurações deste produto de teste usam
        # exatamente o mesmo conteúdo fornecido à CLI.
        release_config = product.release_configuration.first()
        assert release_config is not None
        assert release_config.data == config, (
            "A configuração padrão do Service difere da configuração da CLI",
            release_config.data,
            config,
        )

        payload = json.loads(
            (REFERENCE / "full" / "service-payload.json").read_text()
        )
        url = (
            f"/api/v1/organizations/{org.id}"
            f"/products/{product.id}"
            f"/repositories/{repository.id}"
            "/calculate/math-model/"
        )

        response = self.client.post(url, payload, format="json")
        assert response.status_code == 201, (
            response.status_code, response.content.decode()
        )

        actual = {}
        for section, model, key_field in [
            ("measures", CalculatedMeasure, "measure__key"),
            (
                "subcharacteristics",
                CalculatedSubCharacteristic,
                "subcharacteristic__key",
            ),
            (
                "characteristics",
                CalculatedCharacteristic,
                "characteristic__key",
            ),
        ]:
            actual[section] = dict(
                model.objects.filter(repository=repository)
                .values_list(key_field, "value")
            )

        actual["tsqmi"] = {
            "tsqmi": TSQMI.objects.get(repository=repository).value
        }

        print("\nResultado Service:", json.dumps(actual, indent=2))
        for section, values in actual.items():
            cli_values = {
                item["key"]: item["value"]
                for item in expected[section]
            }
            assert values.keys() == cli_values.keys(), (
                section, "Chaves diferentes", values, cli_values
            )
            for key, value in values.items():
                assert value == pytest.approx(
                    cli_values[key], rel=1e-9, abs=1e-12
                ), (section, key, value, cli_values[key])
