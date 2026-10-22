import datetime as dt
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from characteristics.models import CalculatedCharacteristic
from goals.models import Goal
from metrics.models import CollectedMetric
from organizations.management.commands.seed_demo_data import GITHUB_METRICS
from releases.models import Release
from tsqmi.models import TSQMI
from utils.tests import APITestCaseExpanded

COMMAND = "seed_demo_data"


class SeedDemoDataTestCase(APITestCaseExpanded):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="admin"
        )
        self.org = self.get_organization(add_user=False)
        self.product = self.get_product(self.org)
        self.repository = self.get_repository(self.product, name="2022-1-MeasureSoftGram-Service")

    def run_seed(self, days=2, **options):
        out, err = StringIO(), StringIO()
        call_command(COMMAND, days=days, repos=self.repository.name, stdout=out, stderr=err, **options)
        return out.getvalue() + err.getvalue()

    def github_metrics(self, key):
        return CollectedMetric.objects.filter(repository=self.repository, qualifier="TRK", metric__key=key)

    def test_seeds_demo_data_without_grafana(self):
        output = self.run_seed()

        self.assertNotIn("Grafana", output)
        self.assertTrue(CollectedMetric.objects.filter(repository=self.repository).exists())
        self.assertTrue(CalculatedCharacteristic.objects.filter(repository=self.repository).exists())
        self.assertTrue(TSQMI.objects.filter(repository=self.repository).exists())

    def test_short_period_has_at_least_two_analyses(self):
        self.run_seed(days=2)

        self.assertEqual(TSQMI.objects.filter(repository=self.repository).count(), 2)

    def test_seeds_one_analysis_every_three_days_ending_near_end_date(self):
        self.run_seed(days=12)

        dates = list(TSQMI.objects.filter(repository=self.repository).values_list("created_at", flat=True))
        characteristic_dates = set(
            CalculatedCharacteristic.objects.filter(repository=self.repository).values_list("created_at", flat=True)
        )
        # dias 11, 8, 5 e 2 a partir do mais recente, mais o primeiro dia do período
        self.assertEqual(len(dates), 5)
        self.assertEqual(characteristic_dates, set(dates))
        self.assertGreater(max(dates), timezone.now() - dt.timedelta(days=2))

    def test_seeds_github_metrics_on_analyses_dates(self):
        self.run_seed(days=12)

        analyses_dates = set(TSQMI.objects.filter(repository=self.repository).values_list("created_at", flat=True))
        for key in GITHUB_METRICS:
            with self.subTest(key=key):
                metrics = self.github_metrics(key)
                self.assertEqual(metrics.count(), len(analyses_dates))
                self.assertEqual(set(metrics.values_list("created_at", flat=True)), analyses_dates)
                self.assertGreaterEqual(len(set(metrics.values_list("value", flat=True))), 3)
                self.assertFalse(metrics.exclude(path=None).exists())

        total_issues = dict(self.github_metrics("total_issues").values_list("created_at", "value"))
        for created_at, resolved in self.github_metrics("resolved_issues").values_list("created_at", "value"):
            self.assertLessEqual(resolved, total_issues[created_at])

    def test_github_metrics_are_reproducible(self):
        self.run_seed(days=12)
        first = list(self.github_metrics("total_issues").order_by("created_at").values_list("value", flat=True))

        self.run_seed(days=12, clean_all=True, clean_tsqmi=True)
        second = list(self.github_metrics("total_issues").order_by("created_at").values_list("value", flat=True))

        self.assertEqual(first, second)

    def test_clean_all_removes_github_metrics(self):
        self.run_seed(days=12)
        self.run_seed(days=12, clean_all=True, clean_tsqmi=True)

        analyses = TSQMI.objects.filter(repository=self.repository).count()
        for key in GITHUB_METRICS:
            with self.subTest(key=key):
                self.assertEqual(self.github_metrics(key).count(), analyses)

    def test_analysis_distribution_returns_seeded_github_metric(self):
        self.run_seed(days=12)

        self.org.members.add(self.admin)
        goal = Goal.objects.create(created_by=self.admin, product=self.product, data={"reliability": 70})
        release = Release.objects.create(
            release_name="Distribuição",
            start_at=timezone.now() - dt.timedelta(days=13),
            end_at=timezone.now(),
            created_by=self.admin,
            product=self.product,
            goal=goal,
        )
        client = APIClient()
        client.force_authenticate(self.admin, token=Token.objects.create(user=self.admin))

        response = client.get(
            f"/api/v1/organizations/{self.org.id}/products/{self.product.id}/analysis-distribution/",
            {
                "release_id": release.id,
                "repository_id": self.repository.id,
                "level": "metric",
                "key": "total_issues",
            },
        )

        self.assertEqual(response.status_code, 200)
        analyses = response.json()["entity"]["analyses"]
        self.assertEqual(len(analyses), self.github_metrics("total_issues").count())
        self.assertGreaterEqual(len({analysis["value"] for analysis in analyses}), 3)
        self.assertEqual(response.json()["entity"]["metric_type"], "INT")
