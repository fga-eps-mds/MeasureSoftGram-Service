from datetime import timedelta

from django.utils import timezone

from goals.models import Goal
from metrics.distribution import get_repository_distribution
from metrics.models import CollectedMetric, SupportedMetric
from releases.models import Release
from utils.tests import APITestCaseExpanded


class RepositoryDistributionTestCase(APITestCaseExpanded):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.repository = self.get_repository(self.product)
        self.now = timezone.now()
        goal = Goal.objects.create(
            created_by=self.user,
            product=self.product,
            data={"reliability": 50, "maintainability": 50},
        )
        self.release = Release.objects.create(
            release_name="R1",
            start_at=self.now - timedelta(days=10),
            end_at=self.now,
            created_by=self.user,
            product=self.product,
            goal=goal,
        )

    def collect(self, key, path, value, created_at, qualifier="FIL"):
        return CollectedMetric.objects.create(
            metric=SupportedMetric.objects.get(key=key),
            value=value,
            path=path,
            qualifier=qualifier,
            repository=self.repository,
            created_at=created_at,
        )

    def test_uses_latest_collection_in_release_window(self):
        old = self.now - timedelta(days=5)
        latest = self.now - timedelta(days=1)
        after_release = self.now + timedelta(days=1)
        self.collect("coverage", "src/a.py", 10.0, old)
        self.collect("coverage", "src/a.py", 80.0, latest)
        anchor = self.collect("coverage", "src/b.py", 60.0, latest)
        self.collect("coverage", None, 70.0, latest, qualifier="TRK")
        self.collect("coverage", "src/a.py", 0.0, after_release)

        result = get_repository_distribution(self.repository, "coverage", self.release)

        self.assertEqual(
            result["files"],
            [{"path": "src/a.py", "value": 80.0}, {"path": "src/b.py", "value": 60.0}],
        )
        self.assertEqual(result["collected_at"], anchor.created_at)
        self.assertEqual(result["excluded_files"], 0)
        self.assertEqual(result["summary"]["count"], 2)
        self.assertAlmostEqual(result["summary"]["mean"], 70.0)

    def test_excludes_files_without_lines_of_code(self):
        at = self.now - timedelta(days=1)
        for path, coverage, ncloc in (("src/a.py", 80.0, 120), ("src/b.py", 0.0, 0), ("src/c.py", 50.0, 30)):
            self.collect("coverage", path, coverage, at)
            self.collect("ncloc", path, ncloc, at)

        result = get_repository_distribution(self.repository, "coverage", self.release)

        self.assertEqual([f["path"] for f in result["files"]], ["src/a.py", "src/c.py"])
        self.assertEqual(result["excluded_files"], 1)
        self.assertEqual(result["summary"]["count"], 2)

    def test_keeps_latest_value_when_collections_are_close(self):
        self.collect("coverage", "src/a.py", 10.0, self.now - timedelta(days=1, minutes=10))
        self.collect("coverage", "src/a.py", 20.0, self.now - timedelta(days=1))

        result = get_repository_distribution(self.repository, "coverage", self.release)

        self.assertEqual(result["files"], [{"path": "src/a.py", "value": 20.0}])

    def test_repository_without_file_data_in_release(self):
        self.collect("coverage", "src/a.py", 80.0, self.now + timedelta(days=1))

        result = get_repository_distribution(self.repository, "coverage", self.release)

        self.assertEqual(
            result,
            {"collected_at": None, "excluded_files": 0, "summary": None, "files": []},
        )

    def test_includes_ncloc_written_right_after_the_metric(self):
        at = self.now - timedelta(days=1)
        self.collect("coverage", "src/a.py", 80.0, at)
        self.collect("coverage", "src/b.py", 0.0, at)
        self.collect("ncloc", "src/a.py", 120, at + timedelta(microseconds=1))
        self.collect("ncloc", "src/b.py", 0, at + timedelta(microseconds=2))

        result = get_repository_distribution(self.repository, "coverage", self.release)

        self.assertEqual(result["files"], [{"path": "src/a.py", "value": 80.0}])
        self.assertEqual(result["excluded_files"], 1)

    def test_latest_collection_without_the_metric_has_no_files(self):
        self.collect("coverage", "src/a.py", 80.0, self.now - timedelta(days=3))
        latest = self.collect("ncloc", "src/a.py", 120, self.now - timedelta(days=1))

        result = get_repository_distribution(self.repository, "coverage", self.release)

        self.assertEqual(
            result,
            {"collected_at": latest.created_at, "excluded_files": 0, "summary": None, "files": []},
        )

    def test_ignores_file_rows_without_path(self):
        at = self.now - timedelta(days=1)
        self.collect("coverage", "src/a.py", 80.0, at)
        self.collect("coverage", None, 10.0, at)

        result = get_repository_distribution(self.repository, "coverage", self.release)

        self.assertEqual(result["files"], [{"path": "src/a.py", "value": 80.0}])

    def test_includes_collection_on_last_day_of_release(self):
        end_day = timezone.localtime(self.now).replace(hour=0, minute=0, second=0, microsecond=0)
        self.release.end_at = end_day
        self.release.save()
        self.collect("coverage", "src/a.py", 80.0, end_day + timedelta(hours=15))

        result = get_repository_distribution(self.repository, "coverage", self.release)

        self.assertEqual(result["files"], [{"path": "src/a.py", "value": 80.0}])
