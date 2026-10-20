from django.test import SimpleTestCase

from metrics.distribution import summarize


class SummarizeTestCase(SimpleTestCase):
    def test_summary_of_known_values(self):
        summary = summarize([8, 1, 7, 2, 6, 3, 5, 4])

        self.assertEqual(summary["count"], 8)
        self.assertEqual(summary["min"], 1)
        self.assertEqual(summary["max"], 8)
        self.assertAlmostEqual(summary["q1"], 2.75)
        self.assertAlmostEqual(summary["median"], 4.5)
        self.assertAlmostEqual(summary["q3"], 6.25)
        self.assertAlmostEqual(summary["mean"], 4.5)
        # desvio padrão populacional de 1..8 = sqrt(63 / 12) = sqrt(5.25)
        self.assertAlmostEqual(summary["std_dev"], 2.29128784747792)

    def test_single_value(self):
        summary = summarize([3.0])

        self.assertEqual(summary["count"], 1)
        for key in ("min", "q1", "median", "q3", "max", "mean"):
            self.assertEqual(summary[key], 3.0)
        self.assertEqual(summary["std_dev"], 0.0)

    def test_empty_list_has_no_summary(self):
        self.assertIsNone(summarize([]))
