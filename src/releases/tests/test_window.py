from datetime import timedelta

from django.utils import timezone

from goals.models import Goal
from metrics.models import CollectedMetric, SupportedMetric
from releases.models import Release
from releases.service import filter_release_window
from utils.tests import APITestCaseExpanded


class FilterReleaseWindowTestCase(APITestCaseExpanded):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.repository = self.get_repository(self.product)
        goal = Goal.objects.create(
            created_by=self.user,
            product=self.product,
            data={"reliability": 50, "maintainability": 50},
        )
        today = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0)
        self.start_day = today - timedelta(days=10)
        self.end_day = self.start_day + timedelta(days=10)
        self.release = Release.objects.create(
            release_name="R1",
            start_at=self.start_day,
            end_at=self.end_day,
            created_by=self.user,
            product=self.product,
            goal=goal,
        )
        self.metric = SupportedMetric.objects.get(key="coverage")

    def collect(self, created_at):
        return CollectedMetric.objects.create(
            metric=self.metric,
            value=1.0,
            path="src/a.py",
            qualifier="FIL",
            repository=self.repository,
            created_at=created_at,
        )

    def window(self):
        return filter_release_window(CollectedMetric.objects.all(), self.release)

    def test_excludes_values_outside_the_window(self):
        self.collect(self.start_day - timedelta(minutes=1))
        self.collect(self.end_day + timedelta(days=1))

        self.assertEqual(list(self.window()), [])

    def test_includes_both_bound_days(self):
        at_start = self.collect(self.start_day)
        at_end = self.collect(self.end_day)

        self.assertCountEqual(self.window(), [at_start, at_end])

    def test_includes_later_time_on_the_last_day(self):
        late = self.collect(self.end_day + timedelta(hours=15))

        self.assertCountEqual(self.window(), [late])
