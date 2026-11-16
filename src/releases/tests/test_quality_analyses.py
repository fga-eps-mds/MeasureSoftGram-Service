from datetime import timedelta

from django.test import override_settings
from django.utils import timezone

from characteristics.models import CalculatedCharacteristic
from math_model.models import QualityAnalysis
from math_model.tests import test_quality_analysis_model as fixtures
from releases.analyses import get_latest_release_analyses, get_release_analyses_history
from releases.service import get_accomplished_values


class ReleaseAnalysisTest(fixtures.QualityAnalysisModelTest):
    def test_partial_latest_analysis_does_not_borrow_previous_values(self):
        old = QualityAnalysis.objects.create(repository=self.repository, release=self.release)
        self._create_five_layers(old)
        newest = QualityAnalysis.objects.create(
            repository=self.repository,
            release=self.release,
            is_partial=True,
            created_at=old.created_at + timedelta(seconds=1),
        )
        self.assertEqual(list(get_latest_release_analyses(self.release, [self.repository.pk])), [newest])
        self.assertEqual(get_accomplished_values(self.release, [self.repository.pk]), [])

    def test_release_dates_do_not_reassign_analyses_and_equal_times_use_id(self):
        at = timezone.now()
        analyses = [
            QualityAnalysis.objects.create(
                repository=self.repository,
                release=self.release,
                created_at=at,
            )
            for _ in range(2)
        ]
        self._create_five_layers(analyses[1])
        self.release.start_at = at + timedelta(days=30)
        self.release.end_at = at + timedelta(days=31)
        self.release.save()
        with self.assertNumQueries(1):
            self.assertEqual(list(get_latest_release_analyses(self.release, [self.repository.pk])), [analyses[1]])
        self.assertEqual(list(get_release_analyses_history(self.release, [self.repository.pk])), analyses)
        self.assertTrue(get_accomplished_values(self.release, [self.repository.pk]))
        other = self.get_repository(self.product, name="other")
        QualityAnalysis.objects.create(repository=other, release=self.release)
        self.assertEqual(list(get_latest_release_analyses(self.release, [self.repository.pk])), [analyses[1]])

    @override_settings(AMBIENT_TEST_OR_DEV=False)
    def test_release_app_has_no_scheduler_startup_hook(self):
        from releases.apps import ReleasesConfig
        from django.apps import AppConfig

        self.assertIs(ReleasesConfig.ready, AppConfig.ready)

    def test_final_model_has_no_redundant_release(self):
        self.assertNotIn("release", {field.name for field in CalculatedCharacteristic._meta.fields})
