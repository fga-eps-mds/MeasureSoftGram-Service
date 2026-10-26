"""
Arquivos com só parte das métricas do SonarQube (TASK21.03.03).

No apache_struts, 122 arquivos .jsp têm `complexity`, mas não têm
`functions`. O msgram-core emparelha as listas dessas métricas pela
posição, então o Service precisa mandá-las alinhadas por caminho.
"""

import copy
import json
from unittest import mock

from django.contrib.auth import get_user_model
from util.exceptions import MeasureSoftGramCoreException

from math_model.services import MathModelServices
from math_model.tests.test_request_body_size import _payload
from measures.models import CalculatedMeasure, SupportedMeasure
from metrics.models import CollectedMetric, SupportedMetric
from utils.tests import APITestCaseExpanded

TOTAL_FILES = 5


def _base_payload():
    payload = _payload()
    components = payload["sonarqube"]["components"][:TOTAL_FILES]
    payload["sonarqube"]["components"] = components
    payload["sonarqube"]["paging"].update(pageSize=TOTAL_FILES, total=TOTAL_FILES)
    return payload


def _jsp_component():
    """Arquivo .jsp com `complexity`, mas sem `functions`."""
    path = "core/src/main/resources/template/simple/form.jsp"
    return {
        "key": f"apache_struts:{path}",
        "name": "form.jsp",
        "qualifier": "FIL",
        "path": path,
        "language": "jsp",
        "measures": [
            {"metric": "complexity", "value": "7", "bestValue": False},
            {"metric": "ncloc", "value": "40", "bestValue": False},
        ],
    }


class CalculateMathModelPartialFileMetricsTest(APITestCaseExpanded):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="task21-03-03-partial", password="test-only"
        )
        self.client.force_authenticate(user=self.user)
        org = self.get_organization()
        self.product = self.get_product(org)
        self.repository = self.get_repository(self.product)
        self.org = org

    def _url(self, repository):
        return (
            f"/api/v1/organizations/{self.org.id}"
            f"/products/{self.product.id}"
            f"/repositories/{repository.id}"
            "/calculate/math-model/"
        )

    def _post(self, repository, payload):
        return self.client.post(
            self._url(repository), json.dumps(payload), content_type="application/json"
        )

    def _non_complex_file_density(self, repository):
        return (
            CalculatedMeasure.objects.filter(
                repository=repository, measure__key="non_complex_file_density"
            )
            .latest("created_at")
            .value
        )

    def test_file_without_functions_is_left_out(self):
        complete = _base_payload()
        partial = copy.deepcopy(complete)
        partial["sonarqube"]["components"].append(_jsp_component())

        response = self._post(self.repository, partial)
        assert response.status_code == 201, response.content.decode()[:500]

        reference_repository = self.get_repository(self.product, name="referencia")
        response = self._post(reference_repository, complete)
        assert response.status_code == 201, response.content.decode()[:500]

        assert self._non_complex_file_density(self.repository) == (
            self._non_complex_file_density(reference_repository)
        )

    def test_core_error_returns_400(self):
        with mock.patch(
            "math_model.services.calculate_measures",
            side_effect=MeasureSoftGramCoreException("falha no core"),
        ):
            response = self._post(self.repository, _base_payload())

        assert response.status_code == 400, response.content.decode()[:500]
        assert response.json() == {"error": "falha no core"}


class ResolveMetricParamsByPathTest(APITestCaseExpanded):
    def _metric(self, key, path, value):
        return CollectedMetric(
            metric=SupportedMetric.objects.get(key=key),
            value=value,
            qualifier="FIL",
            path=path,
        )

    def test_pairs_by_path_not_by_position(self):
        # listas do mesmo tamanho, mas faltando arquivos diferentes em cada uma
        collected = [
            self._metric("complexity", "a.java", 10),
            self._metric("complexity", "b.java", 20),
            self._metric("functions", "c.java", 3),
            self._metric("functions", "b.java", 4),
        ]
        measure = SupportedMeasure.objects.get(key="non_complex_file_density")

        params = MathModelServices._resolve_metric_params_in_memory(
            measure, MathModelServices._index_metrics_by_key(collected)
        )

        assert params == {"complexity": [20], "functions": [4]}
