"""
Tamanho do corpo aceito pelo cálculo do modelo (TASK21.03.03.01).

Com a paginação da TASK21.03.03, a Action manda ao calculate/math-model/
todos os componentes do SonarQube, cerca de 870 bytes por componente. O
padrão do Django para DATA_UPLOAD_MAX_MEMORY_SIZE (2,5 MiB) recusa com 400,
antes de a view rodar, os repositórios com mais de cerca de 3.000
componentes.
"""

import json

from django.conf import global_settings
from django.contrib.auth import get_user_model

from metrics.models import CollectedMetric
from utils.tests import APITestCaseExpanded


# Cerca de 3,1 MB, acima do padrão de 2,5 MiB e dos 3.037 componentes do
# apache_struts, o primeiro repositório recusado com esse limite.
TOTAL_FILES = 4000

FILE_METRICS = {
    "functions": "12",
    "complexity": "34",
    "comment_lines_density": "18.5",
    "duplicated_lines_density": "2.3",
    "coverage": "76.4",
    "ncloc": "250",
    "security_rating": "1.0",
    "reliability_rating": "1.0",
}


def _file_component(index):
    """Componente FIL no formato do /api/measures/component_tree."""
    path = f"src/main/java/org/apache/struts2/module_{index:05d}/ActionSupport.java"
    return {
        "key": f"apache_struts:{path}",
        "name": "ActionSupport.java",
        "qualifier": "FIL",
        "path": path,
        "language": "java",
        "measures": [
            {"metric": metric, "value": value, "bestValue": False}
            for metric, value in FILE_METRICS.items()
        ],
    }


def _payload():
    return {
        "github": {
            "metrics": [
                {"name": "total_issues", "value": 10},
                {"name": "resolved_issues", "value": 8},
                {"name": "sum_ci_feedback_times", "value": 300},
                {"name": "total_builds", "value": 5},
            ],
        },
        "sonarqube": {
            "paging": {"pageIndex": 1, "pageSize": TOTAL_FILES, "total": TOTAL_FILES},
            "baseComponent": {
                "key": "apache_struts",
                "qualifier": "TRK",
                "measures": [],
            },
            "components": [_file_component(i) for i in range(TOTAL_FILES)],
        },
    }


class CalculateMathModelBodySizeTest(APITestCaseExpanded):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="task21-03-03-01", password="test-only"
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

    def test_accepts_body_larger_than_django_default(self):
        body = json.dumps(_payload())
        size = len(body.encode())
        assert size > global_settings.DATA_UPLOAD_MAX_MEMORY_SIZE, size

        response = self.client.post(self.url, body, content_type="application/json")

        assert response.status_code == 201, (
            response.status_code, response.content.decode()[:500]
        )
        saved_paths = (
            CollectedMetric.objects.filter(repository=self.repository, qualifier="FIL")
            .values("path")
            .distinct()
            .count()
        )
        assert saved_paths == TOTAL_FILES
