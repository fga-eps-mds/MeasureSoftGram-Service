from django.test import SimpleTestCase

from releases.service import calculate_diff, calculate_norm_diff, get_norm_diff

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

    def test_returns_none_when_planned_values_are_all_zero(self):
        # a diferença normalizada divide pela norma do planejado: com a meta em 0 ela seria inf
        zero_goal = [{"name": "reliability", "value": 0}, {"name": "maintainability", "value": 0}]
        accomplished = [
            {"name": "reliability", "value": 0.5},
            {"name": "maintainability", "value": 0.5},
        ]

        with self.assertLogs("releases.service", level="WARNING") as logs:
            result = calculate_norm_diff(zero_goal, accomplished)

        self.assertIsNone(result)
        self.assertIn("all zero", logs.output[0])


class CalculateDiffTestCase(SimpleTestCase):
    def test_aligns_planned_and_accomplished_by_name(self):
        accomplished = [
            {
                "repository_name": "repo",
                "characteristics": [
                    {"name": "maintainability", "value": 0.2},
                    {"name": "reliability", "value": 0.7},
                ],
            }
        ]

        result = calculate_diff(PLANNED, accomplished)

        diffs = {c["name"]: c["diff"] for c in result[0]["characteristics"]}
        self.assertAlmostEqual(diffs["maintainability"], 0.3)
        self.assertEqual(diffs["reliability"], 0)

    def test_unplanned_characteristic_gets_no_diff_and_does_not_raise(self):
        accomplished = [
            {
                "repository_name": "repo",
                "characteristics": [
                    {"name": "reliability", "value": 0.4},
                    {"name": "security", "value": 0.9},
                    {"name": "maintainability", "value": 0.5},
                ],
            }
        ]

        result = calculate_diff(PLANNED, accomplished)

        diffs = {c["name"]: c["diff"] for c in result[0]["characteristics"]}
        self.assertAlmostEqual(diffs["reliability"], 0.1)
        self.assertEqual(diffs["maintainability"], 0)
        self.assertIsNone(diffs["security"])


class GetNormDiffTestCase(SimpleTestCase):
    def test_ignores_unplanned_characteristics(self):
        accomplished = [
            {
                "repository_name": "repo",
                "characteristics": [
                    {"name": "reliability", "value": 0.5},
                    {"name": "security", "value": 0.9},
                    {"name": "maintainability", "value": 0.5},
                ],
            }
        ]

        result = get_norm_diff(PLANNED, accomplished)

        self.assertEqual(result[0]["norm_diff"], 0)
