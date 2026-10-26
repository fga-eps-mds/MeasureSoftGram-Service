import copy
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from goals.models import Goal
from measures.models import SupportedMeasure
from metrics.models import SupportedMetric
from organizations.models import Product
from organizations.serializers import ProductSerializer
from release_configuration.models import ReleaseConfiguration
from releases.models import Release
from utils import staticfiles
from utils.tests import APITestCaseExpanded


class QualityModelTreeEndpointTestCase(APITestCaseExpanded):
    def setUp(self):
        self.client = APIClient()
        self.user = self.get_or_create_test_user()
        self.token = Token.objects.create(user=self.user)
        self.client.force_authenticate(self.user, token=self.token)

        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.goal = Goal.objects.create(
            created_at=timezone.now(),
            created_by=self.user,
            product=self.product,
            data={"reliability": 50, "maintainability": 50},
        )
        self.url = (
            f"/api/v1/organizations/{self.org.id}/products/{self.product.id}/quality-model-tree/"
        )

    def test_quality_model_tree_without_release_id_uses_current_config(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

        root = data[0]
        self.assertIsNone(root["id"])
        self.assertEqual(root["type"], "tsqmi")
        self.assertEqual(root["key"], "tsqmi")
        self.assertEqual(root["name"], "TSQMI")
        self.assertEqual(root["weight"], 100)
        self.assertIn("Total Software Quality Measurement Index", root["description"])
        self.assertTrue(len(root["children"]) > 0)

        # Verifica hierarquia: características -> subcaracterísticas -> medidas -> métricas
        first_char = root["children"][0]
        self.assertEqual(first_char["type"], "characteristic")
        self.assertIsNotNone(first_char["id"])
        self.assertIsNotNone(first_char["key"])
        self.assertIsNotNone(first_char["name"])
        self.assertIsNotNone(first_char["weight"])
        self.assertTrue(len(first_char["children"]) > 0)

        first_subchar = first_char["children"][0]
        self.assertEqual(first_subchar["type"], "subcharacteristic")
        self.assertIsNotNone(first_subchar["id"])
        self.assertIsNotNone(first_subchar["key"])
        self.assertIsNotNone(first_subchar["name"])
        self.assertIsNotNone(first_subchar["weight"])
        self.assertTrue(len(first_subchar["children"]) > 0)

        first_measure = first_subchar["children"][0]
        self.assertEqual(first_measure["type"], "measure")
        self.assertIsNotNone(first_measure["id"])
        self.assertIsNotNone(first_measure["key"])
        self.assertIsNotNone(first_measure["name"])
        self.assertIsNotNone(first_measure["weight"])
        self.assertIn("min_threshold", first_measure)
        self.assertIn("max_threshold", first_measure)

        if first_measure["children"]:
            first_metric = first_measure["children"][0]
            self.assertEqual(first_metric["type"], "metric")
            self.assertIsNotNone(first_metric["id"])
            self.assertIsNotNone(first_metric["key"])
            self.assertIsNotNone(first_metric["name"])
            self.assertIsNone(first_metric["weight"])
            self.assertEqual(first_metric["children"], [])

    def test_quality_model_tree_with_release_id_selects_expected_config(self):
        now = timezone.now()
        t1 = now - timedelta(days=30)
        t2 = now - timedelta(days=10)

        # Limpa configurações existentes criadas no save do produto
        self.product.release_configuration.all().delete()

        # Config 1 (mais antiga)
        data_c1 = copy.deepcopy(staticfiles.DEFAULT_PRE_CONFIG)
        data_c1["characteristics"][0]["weight"] = 40
        data_c1["characteristics"][1]["weight"] = 30
        data_c1["characteristics"][2]["weight"] = 30
        ReleaseConfiguration.objects.create(
            name="Config 1",
            data=data_c1,
            product=self.product,
            created_at=t1,
        )

        # Config 2 (mais recente)
        data_c2 = copy.deepcopy(staticfiles.DEFAULT_PRE_CONFIG)
        data_c2["characteristics"][0]["weight"] = 60
        data_c2["characteristics"][1]["weight"] = 20
        data_c2["characteristics"][2]["weight"] = 20
        ReleaseConfiguration.objects.create(
            name="Config 2",
            data=data_c2,
            product=self.product,
            created_at=t2,
        )

        # Release 1: end_at fica entre t1 e t2 -> deve pegar Config 1
        release1 = Release.objects.create(
            release_name="Release 1",
            start_at=t1 - timedelta(days=5),
            end_at=now - timedelta(days=20),
            product=self.product,
            goal=self.goal,
            created_by=self.user,
        )

        # Release 2: end_at fica após t2 -> deve pegar Config 2
        release2 = Release.objects.create(
            release_name="Release 2",
            start_at=t2 - timedelta(days=2),
            end_at=now,
            product=self.product,
            goal=self.goal,
            created_by=self.user,
        )

        # Consulta para release 1
        resp1 = self.client.get(f"{self.url}?release_id={release1.id}")
        self.assertEqual(resp1.status_code, 200)
        tree1 = resp1.json()
        char0_w1 = tree1[0]["children"][0]["weight"]
        self.assertEqual(char0_w1, 40)

        # Consulta para release 2
        resp2 = self.client.get(f"{self.url}?release_id={release2.id}")
        self.assertEqual(resp2.status_code, 200)
        tree2 = resp2.json()
        char0_w2 = tree2[0]["children"][0]["weight"]
        self.assertEqual(char0_w2, 60)

    def test_quality_model_tree_fallback_to_oldest_config_when_end_at_prior(self):
        now = timezone.now()
        t1 = now - timedelta(days=20)
        t2 = now - timedelta(days=10)

        self.product.release_configuration.all().delete()

        data_c1 = copy.deepcopy(staticfiles.DEFAULT_PRE_CONFIG)
        data_c1["characteristics"][0]["weight"] = 45
        data_c1["characteristics"][1]["weight"] = 25
        data_c1["characteristics"][2]["weight"] = 30
        ReleaseConfiguration.objects.create(
            name="Oldest Config",
            data=data_c1,
            product=self.product,
            created_at=t1,
        )

        data_c2 = copy.deepcopy(staticfiles.DEFAULT_PRE_CONFIG)
        data_c2["characteristics"][0]["weight"] = 55
        data_c2["characteristics"][1]["weight"] = 25
        data_c2["characteristics"][2]["weight"] = 20
        ReleaseConfiguration.objects.create(
            name="Newest Config",
            data=data_c2,
            product=self.product,
            created_at=t2,
        )

        # Release com end_at anterior a todas as configurações (t1 - 10 dias)
        release_old = Release.objects.create(
            release_name="Ancient Release",
            start_at=t1 - timedelta(days=30),
            end_at=t1 - timedelta(days=10),
            product=self.product,
            goal=self.goal,
            created_by=self.user,
        )

        resp = self.client.get(f"{self.url}?release_id={release_old.id}")
        self.assertEqual(resp.status_code, 200)
        tree = resp.json()
        char0_w = tree[0]["children"][0]["weight"]
        # Deve ter pego a mais antiga (45)
        self.assertEqual(char0_w, 45)

    def test_quality_model_tree_product_without_config_returns_empty_list(self):
        # Remove qualquer release_configuration existente (CA7)
        self.product.release_configuration.all().delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_quality_model_tree_invalid_release_id_format(self):
        response = self.client.get(f"{self.url}?release_id=abc")
        self.assertEqual(response.status_code, 400)
        self.assertIn("release_id", response.json().get("detail", ""))

    def test_quality_model_tree_nonexistent_release_id(self):
        response = self.client.get(f"{self.url}?release_id=999999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Release não encontrada", response.json().get("detail", ""))

    def test_quality_model_tree_release_id_from_other_product(self):
        other_product = self.get_product(self.org, name="Other Product")
        other_goal = Goal.objects.create(
            created_at=timezone.now(),
            created_by=self.user,
            product=other_product,
            data={"reliability": 50, "maintainability": 50},
        )
        other_release = Release.objects.create(
            release_name="Other Release",
            start_at=timezone.now() - timedelta(days=10),
            end_at=timezone.now(),
            product=other_product,
            goal=other_goal,
            created_by=self.user,
        )

        # Tenta consultar no endpoint de self.product usando a release do other_product
        response = self.client.get(f"{self.url}?release_id={other_release.id}")
        self.assertEqual(response.status_code, 404)

    def test_quality_model_tree_user_not_member_of_org_returns_404(self):
        other_user = get_user_model().objects.create(
            username="unauthorized-user",
            email="unauth@example.com",
        )
        other_token = Token.objects.create(user=other_user)
        other_client = APIClient()
        other_client.force_authenticate(other_user, token=other_token)

        response = other_client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_quality_model_tree_unauthenticated_returns_401(self):
        anonymous_client = APIClient()
        response = anonymous_client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_quality_model_tree_metric_shared_across_measures(self):
        # CA6: Uma métrica usada por mais de uma medida aparece sob cada uma
        metric = SupportedMetric.objects.first()
        measures = list(SupportedMeasure.objects.all()[:2])
        self.assertGreaterEqual(len(measures), 2)
        measures[0].metrics.add(metric)
        measures[1].metrics.add(metric)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        tree = response.json()

        # Percorre a árvore buscando a métrica sob cada medida
        found_in_measures = []
        for char in tree[0]["children"]:
            for subchar in char["children"]:
                for measure in subchar["children"]:
                    for m in measure["children"]:
                        if m["key"] == metric.key:
                            found_in_measures.append(measure["key"])

        self.assertIn(measures[0].key, found_in_measures)
        self.assertIn(measures[1].key, found_in_measures)

    def test_quality_model_tree_action_link_in_product_detail(self):
        serializer = ProductSerializer(self.product, context={"request": None})
        actions = serializer.get_actions(self.product)
        self.assertIn("get quality model tree", actions)
        self.assertIn(
            f"/api/v1/organizations/{self.org.id}/products/{self.product.id}/quality-model-tree/",
            actions["get quality model tree"],
        )

    def test_quality_model_tree_entities_outside_config_do_not_appear(self):
        # CA6: Entidades que não fazem parte da configuração da release não aparecem
        self.product.release_configuration.all().delete()

        custom_data = {
            "characteristics": [
                {
                    "key": "reliability",
                    "weight": 100,
                    "subcharacteristics": [
                        {
                            "key": "testing_status",
                            "weight": 100,
                            "measures": [
                                {
                                    "key": "passed_tests",
                                    "weight": 100,
                                    "min_threshold": 0,
                                    "max_threshold": 1,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        ReleaseConfiguration.objects.create(
            name="Reliability Only",
            data=custom_data,
            product=self.product,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        tree = response.json()

        char_keys = [c["key"] for c in tree[0]["children"]]
        self.assertEqual(char_keys, ["reliability"])
        self.assertNotIn("maintainability", char_keys)

        subchar_keys = [s["key"] for s in tree[0]["children"][0]["children"]]
        self.assertEqual(subchar_keys, ["testing_status"])
        self.assertNotIn("maturity", subchar_keys)

        measure_keys = [
            m["key"] for m in tree[0]["children"][0]["children"][0]["children"]
        ]
        self.assertEqual(measure_keys, ["passed_tests"])
        self.assertNotIn("test_builds", measure_keys)
