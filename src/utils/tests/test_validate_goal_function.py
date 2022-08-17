from django.test import TestCase
from parameterized import parameterized

# from utils import validate_goal_function


def validate_goal_function(goal_dict):
    return False


GOALS = [
    (
        {
            'reliability': 50,
            'maintainability': 50,
        },
        True,
    ),
    (
        {
            'reliability': 50,
            'maintainability': 50,
            'Non-Supported-Characteristic': 50,
        },
        False,
    ),
    (
        {
            'reliability': 50,
            'maintainability': 50,
            10: 50,
        },
        False,
    ),
    (
        {
            'functional_suitability': 50,
            'performance_efficiency': 50,
            'usability': 50,
            'compatibility': 50,
            'reliability': 50,
            'security': 50,
            'maintainability': 50,
            'portability': 50,
        },
        True,
    ),
    (
        {
            'functional_suitability': 0,
            'performance_efficiency': 100,
            'usability': 0,
            'compatibility': 0,
            'reliability': 0,
            'security': 100,
            'maintainability': 0,
            'portability': 0,
        },
        True,
    ),
]


class ValidateGoalFunctionTestCase(TestCase):

    @parameterized.expand(GOALS)
    def test_if_validate_goal_is_detecting_unssuported_characteristics(
        self,
        goal_dict,
        expected_result,
    ):
        self.assertEqual(validate_goal_function(goal_dict), expected_result)

    @parameterized.expand(GOALS)
    def test_if_validate_goal_is_detecting_wrong_weights(
        self,
        goal_dict,
        expected_result,
    ):
        self.assertEqual(validate_goal_function(goal_dict), expected_result)
