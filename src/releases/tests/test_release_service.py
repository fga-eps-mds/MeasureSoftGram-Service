from django.test import SimpleTestCase

from releases.service import calculate_norm_diff

PLANNED = [
    {"name": "reliability", "value": 0.5},
    {"name": "maintainability", "value": 0.5},
]


class CalculateNormDiffTestCase(SimpleTestCase):
    def test_returns_value_when_inputs_are_valid(self):
        accomplished = [
            {"name": "reliability", "value": 0.5},
            {"name": "maintainability", "value": 0.5},
        ]

        self.assertIsNotNone(calculate_norm_diff(PLANNED, accomplished))

    def test_returns_none_when_sizes_differ(self):
        with self.assertLogs("releases.service", level="WARNING") as logs:
            result = calculate_norm_diff(PLANNED, [{"name": "reliability", "value": 0.5}])

        self.assertIsNone(result)
        self.assertIn("should be the same", logs.output[0])

    def test_returns_none_when_planned_characteristic_is_missing(self):
        accomplished = [
            {"name": "reliability", "value": 0.5},
            {"name": "usability", "value": 0.5},
        ]

        with self.assertLogs("releases.service", level="WARNING") as logs:
            result = calculate_norm_diff(PLANNED, accomplished)

        self.assertIsNone(result)
        self.assertIn("maintainability was not found", logs.output[0])

    def test_returns_none_when_value_is_out_of_range(self):
        accomplished = [
            {"name": "reliability", "value": 1.5},
            {"name": "maintainability", "value": 0.5},
        ]

        with self.assertLogs("releases.service", level="WARNING") as logs:
            result = calculate_norm_diff(PLANNED, accomplished)

        self.assertIsNone(result)
        self.assertIn("between 0 and 1", logs.output[0])
