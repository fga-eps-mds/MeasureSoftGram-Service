"""Contratos MSG36: cada POST representa uma execução, inclusive fora de release."""

from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from goals.models import Goal
from math_model.models import QualityAnalysis
from math_model.tests import test_atomicity_smoke as smoke
from releases.models import Release


class AnalysisFlowTest(smoke.MathModelAtomicitySmokeTest):
    def active_release(self, name="Release"):
        return Release.objects.create(
            release_name=name,
            product=self.product,
            created_by=self.user,
            goal=Goal.objects.create(product=self.product, created_by=self.user, data={"reliability": 70}),
            start_at=timezone.now() - timedelta(days=1),
            end_at=timezone.now() + timedelta(days=1),
        )

    def test_two_posts_preserve_five_layers_and_release_deletion(self):
        release = self.active_release()
        for _ in range(2):
            response = self.client.post(self.url, smoke._full_payload(), format="json")
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(response.data["release"], release.pk)
        analyses = list(QualityAnalysis.objects.filter(release=release))
        self.assertEqual(len(analyses), 2)
        counts = []
        for analysis in analyses:
            counts.append(
                [
                    getattr(analysis, name).count()
                    for name in (
                        "collected_metrics",
                        "calculated_measures",
                        "calculated_subcharacteristics",
                        "calculated_characteristics",
                        "tsqmis",
                    )
                ]
            )
            self.assertTrue(all(counts[-1]))
            self.assertEqual(analysis.release_configuration_id, self.release_config.pk)
        release.delete()
        for analysis, expected in zip(analyses, counts):
            analysis.refresh_from_db()
            self.assertIsNone(analysis.release_id)
            self.assertEqual(
                [
                    getattr(analysis, name).count()
                    for name in (
                        "collected_metrics",
                        "calculated_measures",
                        "calculated_subcharacteristics",
                        "calculated_characteristics",
                        "tsqmis",
                    )
                ],
                expected,
            )

    def test_outside_release_returns_201_and_warning(self):
        response = self.client.post(self.url, smoke._full_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["release"])
        self.assertIn("warning", response.data)

    def test_null_metric_marks_partial(self):
        payload = smoke._full_payload()
        payload["github"]["metrics"][0]["value"] = None
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        analysis = QualityAnalysis.objects.get(pk=response.data["analysis"])
        self.assertTrue(analysis.is_partial)
        self.assertIn("total_issues", analysis.missing_inputs)

    def test_overlapping_releases_reject_without_writing(self):
        self.active_release("A")
        self.active_release("B")
        before = QualityAnalysis.objects.count()
        response = self.client.post(self.url, smoke._full_payload(), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(QualityAnalysis.objects.count(), before)

    def test_failure_at_persistence_rolls_back_analysis_and_layers(self):
        before = QualityAnalysis.objects.count()
        with patch("math_model.services.CalculatedMeasure.objects.bulk_create", side_effect=RuntimeError("fail")):
            with self.assertRaises(RuntimeError):
                self.client.post(self.url, smoke._full_payload(), format="json")
        self.assertEqual(QualityAnalysis.objects.count(), before)
        self.assertEqual(smoke.CollectedMetric.objects.count(), self.initial_collected)
