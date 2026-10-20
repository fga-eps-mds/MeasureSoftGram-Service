import copy
from datetime import timedelta

from django.utils import timezone

from goals.models import Goal
from metrics.distribution import get_metric_reference
from release_configuration.models import ReleaseConfiguration
from releases.models import Release
from utils.staticfiles import DEFAULT_PRE_CONFIG
from utils.tests import APITestCaseExpanded


def config_with_test_coverage(**thresholds):
    data = copy.deepcopy(DEFAULT_PRE_CONFIG)
    measure = data["characteristics"][0]["subcharacteristics"][0]["measures"][2]
    assert measure["key"] == "test_coverage"
    measure.pop("min_threshold")
    measure.pop("max_threshold")
    measure.update(thresholds)
    return data


class MetricReferenceTestCase(APITestCaseExpanded):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.org = self.get_organization()
        self.product = self.get_product(self.org)  # cria a configuração padrão
        self.now = timezone.now()
        self.goal = Goal.objects.create(
            created_by=self.user,
            product=self.product,
            data={"reliability": 50, "maintainability": 50},
        )
        self.release = Release.objects.create(
            release_name="R1",
            start_at=self.now - timedelta(days=10),
            end_at=self.now + timedelta(hours=1),
            created_by=self.user,
            product=self.product,
            goal=self.goal,
        )

    def test_reference_of_measure_that_uses_the_metric(self):
        self.assertEqual(
            get_metric_reference(self.product, self.release, "coverage"),
            {"measure": "test_coverage", "min_threshold": 60, "max_threshold": 100},
        )
        self.assertEqual(
            get_metric_reference(self.product, self.release, "complexity"),
            {"measure": "non_complex_file_density", "min_threshold": 0, "max_threshold": 10},
        )

    def test_no_reference_when_measure_has_no_thresholds(self):
        ReleaseConfiguration.objects.create(
            product=self.product,
            name="Sem thresholds de cobertura",
            data=config_with_test_coverage(),
        )

        self.assertIsNone(get_metric_reference(self.product, self.release, "coverage"))

    def test_ignores_configuration_created_after_release_end(self):
        ReleaseConfiguration.objects.create(
            product=self.product,
            name="Depois da release",
            data=config_with_test_coverage(min_threshold=70, max_threshold=100),
            created_at=self.now + timedelta(hours=2),
        )

        reference = get_metric_reference(self.product, self.release, "coverage")

        self.assertEqual(reference["min_threshold"], 60)

    def test_falls_back_to_oldest_configuration_when_none_precedes_release_end(self):
        past_release = Release.objects.create(
            release_name="R0",
            start_at=self.now - timedelta(days=30),
            end_at=self.now - timedelta(days=20),
            created_by=self.user,
            product=self.product,
            goal=self.goal,
        )
        ReleaseConfiguration.objects.create(
            product=self.product,
            name="Mais nova",
            data=config_with_test_coverage(min_threshold=70, max_threshold=100),
        )

        reference = get_metric_reference(self.product, past_release, "coverage")

        self.assertEqual(reference["min_threshold"], 60)
