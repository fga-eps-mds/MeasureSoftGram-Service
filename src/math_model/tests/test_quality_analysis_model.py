from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from goals.models import Goal
from math_model.models import QualityAnalysis
from measures.models import CalculatedMeasure, SupportedMeasure
from metrics.models import CollectedMetric, SupportedMetric
from release_configuration.models import ReleaseConfiguration
from releases.models import Release
from subcharacteristics.models import CalculatedSubCharacteristic, SupportedSubCharacteristic
from tsqmi.models import TSQMI
from utils import staticfiles
from utils.tests import APITestCaseExpanded


class QualityAnalysisModelTest(APITestCaseExpanded):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="qa_test_user",
            password="test_password",
        )
        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.repository = self.get_repository(self.product)
        self.goal = Goal.objects.create(
            data={"reliability": 0.8},
            created_by=self.user,
            product=self.product,
        )
        now = timezone.now()
        self.release = Release.objects.create(
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=6),
            release_name="Release 1.0",
            created_by=self.user,
            product=self.product,
            goal=self.goal,
        )
        self.release_config = ReleaseConfiguration.objects.create(
            name="Config test",
            data=staticfiles.DEFAULT_PRE_CONFIG,
            product=self.product,
        )
        self.supported_metric = SupportedMetric.objects.create(key="qa_metric_test", name="QA Metric Test")
        self.supported_measure = SupportedMeasure.objects.create(key="qa_measure_test", name="QA Measure Test")
        self.supported_subchar = SupportedSubCharacteristic.objects.create(
            key="qa_subchar_test",
            name="QA SubChar Test",
        )
        self.supported_char = SupportedCharacteristic.objects.create(key="qa_char_test", name="QA Char Test")

    def _create_five_layers(self, analysis: QualityAnalysis, value: float = 0.8):
        metric = CollectedMetric.objects.create(
            metric=self.supported_metric,
            value=value,
            repository=self.repository,
            analysis=analysis,
        )
        measure = CalculatedMeasure.objects.create(
            measure=self.supported_measure,
            value=value,
            repository=self.repository,
            analysis=analysis,
        )
        subchar = CalculatedSubCharacteristic.objects.create(
            subcharacteristic=self.supported_subchar,
            value=value,
            repository=self.repository,
            analysis=analysis,
        )
        char = CalculatedCharacteristic.objects.create(
            characteristic=self.supported_char,
            value=value,
            repository=self.repository,
            analysis=analysis,
        )
        tsqmi = TSQMI.objects.create(
            value=value,
            repository=self.repository,
            analysis=analysis,
        )
        return metric, measure, subchar, char, tsqmi

    def test_multiple_analyses_for_same_repository_and_release(self):
        analysis_1 = QualityAnalysis.objects.create(
            repository=self.repository,
            release=self.release,
            release_configuration=self.release_config,
        )
        self._create_five_layers(analysis_1, value=0.7)

        analysis_2 = QualityAnalysis.objects.create(
            repository=self.repository,
            release=self.release,
            release_configuration=self.release_config,
        )
        self._create_five_layers(analysis_2, value=0.9)

        self.assertEqual(QualityAnalysis.objects.filter(repository=self.repository, release=self.release).count(), 2)
        self.assertEqual(CalculatedCharacteristic.objects.filter(repository=self.repository).count(), 2)
        self.assertEqual(analysis_1.calculated_characteristics.first().value, 0.7)
        self.assertEqual(analysis_2.calculated_characteristics.first().value, 0.9)

    def test_partial_analysis_without_release(self):
        analysis = QualityAnalysis.objects.create(
            repository=self.repository,
            release=None,
            is_partial=True,
            missing_inputs=["coverage", "tests"],
        )

        self.assertIsNone(analysis.release)
        self.assertTrue(analysis.is_partial)
        self.assertEqual(analysis.missing_inputs, ["coverage", "tests"])

    def test_deleting_quality_analysis_cascades_to_five_layers(self):
        analysis = QualityAnalysis.objects.create(
            repository=self.repository,
            release=self.release,
            release_configuration=self.release_config,
        )
        self._create_five_layers(analysis)

        analysis.delete()

        self.assertEqual(CollectedMetric.objects.filter(repository=self.repository).count(), 0)
        self.assertEqual(CalculatedMeasure.objects.filter(repository=self.repository).count(), 0)
        self.assertEqual(CalculatedSubCharacteristic.objects.filter(repository=self.repository).count(), 0)
        self.assertEqual(CalculatedCharacteristic.objects.filter(repository=self.repository).count(), 0)
        self.assertEqual(TSQMI.objects.filter(repository=self.repository).count(), 0)

    def test_deleting_release_or_config_sets_null_on_quality_analysis(self):
        analysis = QualityAnalysis.objects.create(
            repository=self.repository,
            release=self.release,
            release_configuration=self.release_config,
        )

        self.release.delete()
        self.release_config.delete()
        analysis.refresh_from_db()

        self.assertIsNone(analysis.release)
        self.assertIsNone(analysis.release_configuration)
