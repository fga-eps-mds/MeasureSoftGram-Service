from datetime import datetime

from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import CustomUser
from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from goals.models import Goal
from measures.models import CalculatedMeasure, SupportedMeasure
from metrics.models import CollectedMetric, SupportedMetric
from releases.models import Release
from tsqmi.models import TSQMI
from utils.staticfiles import DEFAULT_PRE_CONFIG
from utils.tests import APITestCaseExpanded


def local_datetime(*args):
    return timezone.make_aware(datetime(*args))


class ReleaseDashboardTestCase(APITestCaseExpanded):
    def setUp(self):
        self.client = APIClient()
        self.user = self.get_or_create_test_user()
        self.client.force_authenticate(self.user, token=Token.objects.create(user=self.user))

        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.api = self.get_repository(self.product, name="api")
        self.web = self.get_repository(self.product, name="web")

        self.goal = Goal.objects.create(
            created_by=self.user,
            product=self.product,
            data={"reliability": 70, "maintainability": 60},
        )
        self.release = self.create_release("v1.0", local_datetime(2026, 3, 1), local_datetime(2026, 3, 31))

        self.product_url = f"/api/v1/organizations/{self.org.id}/products/{self.product.id}/"
        self.summary_url = f"{self.product_url}release-dashboard/summary/"
        self.characteristics_url = f"{self.product_url}release-dashboard/characteristics/"

    def create_release(self, name, start_at, end_at):
        return Release.objects.create(
            release_name=name,
            start_at=start_at,
            end_at=end_at,
            created_by=self.user,
            product=self.product,
            goal=self.goal,
        )

    def calculated_characteristic(self, repository, key, value, created_at):
        return CalculatedCharacteristic.objects.create(
            characteristic=SupportedCharacteristic.objects.get(key=key),
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

    def tsqmi(self, repository, value, created_at):
        return TSQMI.objects.create(repository=repository, value=value, created_at=created_at)

    def client_for(self, user):
        client = APIClient()
        client.force_authenticate(user, token=Token.objects.create(user=user))
        return client

    def member_who_is_not_admin(self):
        member = CustomUser.objects.create(username="member", email="member@example.com")
        self.org.members.add(member)
        return member

    def outsider(self):
        return CustomUser.objects.create(username="outsider", email="outsider@example.com")

    def all_urls(self):
        return [
            (self.summary_url, {"release_id": self.release.id}),
            (self.characteristics_url, {"release_id": self.release.id}),
        ]


class ReleaseSummaryTestCase(ReleaseDashboardTestCase):
    def get_totals(self, release=None):
        response = self.client.get(self.summary_url, {"release_id": (release or self.release).id})
        self.assertEqual(response.status_code, 200)
        return response.json()["totals"]

    def test_entity_totals_count_release_configuration_entities(self):
        characteristics = DEFAULT_PRE_CONFIG["characteristics"]
        subcharacteristics = {sub["key"] for c in characteristics for sub in c["subcharacteristics"]}
        measures = {m["key"] for c in characteristics for sub in c["subcharacteristics"] for m in sub["measures"]}
        metrics = SupportedMetric.objects.filter(related_measures__key__in=measures).distinct().count()

        totals = self.get_totals()

        self.assertEqual(totals["characteristics"], len(characteristics))
        self.assertEqual(totals["subcharacteristics"], len(subcharacteristics))
        self.assertEqual(totals["measures"], len(measures))
        self.assertEqual(totals["metrics"], metrics)

    def test_entity_totals_do_not_count_history_rows(self):
        before = self.get_totals()
        for day in (5, 10, 15):
            self.calculated_characteristic(self.api, "reliability", 0.5, local_datetime(2026, 3, day))
            CalculatedMeasure.objects.create(
                measure=SupportedMeasure.objects.get(key="test_coverage"),
                repository=self.api,
                value=0.5,
                created_at=local_datetime(2026, 3, day),
            )

        after = self.get_totals()

        for total in ("characteristics", "subcharacteristics", "measures", "metrics"):
            self.assertEqual(after[total], before[total])

    def test_repositories_are_the_ones_analyzed_in_the_release_window(self):
        self.tsqmi(self.api, 0.7, local_datetime(2026, 3, 5))
        self.tsqmi(self.api, 0.8, local_datetime(2026, 3, 20))
        self.tsqmi(self.web, 0.6, local_datetime(2026, 4, 2))  # fora da janela

        self.assertEqual(self.get_totals()["repositories"], 1)

    def test_last_day_of_release_counts_as_analyzed(self):
        self.tsqmi(self.web, 0.6, local_datetime(2026, 3, 31, 18, 0))

        self.assertEqual(self.get_totals()["repositories"], 1)

    def test_only_release_repositories_are_counted_when_release_has_them(self):
        self.release.repositories.add(self.api)
        self.tsqmi(self.api, 0.7, local_datetime(2026, 3, 5))
        self.tsqmi(self.web, 0.6, local_datetime(2026, 3, 5))

        self.assertEqual(self.get_totals()["repositories"], 1)

    def test_files_count_distinct_files_and_not_collections(self):
        for day in (5, 20):
            for path in ("src/main.py", "src/utils.py"):
                self.collected_metric(self.api, "coverage", 80, local_datetime(2026, 3, day), "FIL", path)
                self.collected_metric(self.api, "complexity", 3, local_datetime(2026, 3, day), "FIL", path)
        self.collected_metric(self.api, "coverage", 80, local_datetime(2026, 3, 5), "TRK")
        self.collected_metric(self.api, "coverage", 80, local_datetime(2026, 4, 5), "FIL", "src/new.py")

        self.assertEqual(self.get_totals()["files"], 2)

    def test_same_path_in_two_repositories_counts_as_two_files(self):
        self.collected_metric(self.api, "coverage", 80, local_datetime(2026, 3, 5), "FIL", "src/main.py")
        self.collected_metric(self.web, "coverage", 70, local_datetime(2026, 3, 5), "FIL", "src/main.py")

        self.assertEqual(self.get_totals()["files"], 2)

    def test_release_without_analysis_has_zero_repositories_and_files(self):
        totals = self.get_totals()

        self.assertEqual(totals["repositories"], 0)
        self.assertEqual(totals["files"], 0)

    def test_response_identifies_the_release(self):
        response = self.client.get(self.summary_url, {"release_id": self.release.id})

        self.assertEqual(response.json()["release"]["id"], self.release.id)
        self.assertEqual(response.json()["release"]["release_name"], "v1.0")


class ReleaseRepositoriesTsqmiTestCase(ReleaseDashboardTestCase):
    """release-dashboard/characteristics: só o Indicador Total da Qualidade de cada repositório (correções do PO)."""

    def get_data(self):
        response = self.client.get(self.characteristics_url, {"release_id": self.release.id})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_tsqmi_is_latest_value_inside_release_window(self):
        self.tsqmi(self.api, 0.5, local_datetime(2026, 3, 5))
        self.tsqmi(self.api, 0.9, local_datetime(2026, 3, 30))
        self.tsqmi(self.api, 0.1, local_datetime(2026, 4, 2))

        data = self.get_data()
        tsqmi_by_repository = {item["name"]: item["tsqmi"]["value"] for item in data["repositories"]}

        self.assertEqual(tsqmi_by_repository, {"api": 0.9, "web": None})

    def test_returns_only_the_release_and_the_tsqmi_of_each_repository(self):
        # o planejado × realizado e o radar usam o analysis_data da release
        self.calculated_characteristic(self.api, "reliability", 0.8, local_datetime(2026, 3, 5))

        data = self.get_data()

        self.assertEqual(set(data), {"release", "repositories"})
        self.assertEqual(data["release"]["id"], self.release.id)
        for repository in data["repositories"]:
            self.assertEqual(set(repository), {"id", "name", "tsqmi"})

    def test_lists_only_release_repositories_when_release_has_them(self):
        self.release.repositories.add(self.api)

        self.assertEqual([item["name"] for item in self.get_data()["repositories"]], ["api"])


class ReleaseDashboardAccessTestCase(ReleaseDashboardTestCase):
    def test_member_who_is_not_admin_can_access(self):
        client = self.client_for(self.member_who_is_not_admin())

        for url, params in self.all_urls():
            with self.subTest(url=url):
                self.assertEqual(client.get(url, params).status_code, 200)

    def test_user_outside_organization_cannot_access(self):
        client = self.client_for(self.outsider())

        for url, params in self.all_urls():
            with self.subTest(url=url):
                self.assertEqual(client.get(url, params).status_code, 404)

    def test_unauthenticated_user_cannot_access(self):
        client = APIClient()

        for url, params in self.all_urls():
            with self.subTest(url=url):
                self.assertIn(client.get(url, params).status_code, (401, 403))

    def test_release_is_required(self):
        for url in (self.summary_url, self.characteristics_url):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 400)
                self.assertEqual(self.client.get(url, {"release_id": "abc"}).status_code, 400)

    def test_release_of_another_product_returns_404(self):
        other_product = self.get_product(self.org, name="Outro produto")
        other_goal = Goal.objects.create(created_by=self.user, product=other_product, data={"reliability": 50})
        other_release = Release.objects.create(
            release_name="outra",
            start_at=local_datetime(2026, 3, 1),
            end_at=local_datetime(2026, 3, 31),
            created_by=self.user,
            product=other_product,
            goal=other_goal,
        )

        for url in (self.summary_url, self.characteristics_url):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url, {"release_id": other_release.id}).status_code, 404)

    def test_release_history_was_removed(self):
        # a Evolução Temporal e a tela do repositório usam historical-values/* (correções do PO)
        response = self.client.get(
            f"{self.product_url}repositories/{self.api.id}/release-history/", {"level": "characteristic"}
        )

        self.assertEqual(response.status_code, 404)
