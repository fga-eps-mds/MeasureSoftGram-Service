from django.core.management import call_command
from django.test import TestCase

from service.management.commands.utils import (
    create_a_preconfig,
    create_suported_characteristics,
)


class GoalEndpointsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        call_command("load_initial_data")

    def setUp(self):
        characteristics = [
            {
                "key": "functional_suitability",
                "name": "",
                "subcharacteristics": [
                    {"key": "testing_status"},
                ],
            },
            {
                "key": "performance_efficiency",
                "name": "",
                "subcharacteristics": [
                    {"key": "testing_status"},
                ],
            },
            {
                "key": "security",
                "name": "",
                "subcharacteristics": [
                    {"key": "testing_status"},
                ],
            },
        ]
        create_suported_characteristics(characteristics)
        characteristics_keys = [item["key"] for item in characteristics]
        create_a_preconfig(characteristics_keys=characteristics_keys)

    def test_if_create_goal_reject_invalid_jsons(self):
        invalid_json = {
            "release_name": "v1.0.0",
            "start_at": "2022-08-19",
            "end_at": "2022-09-19",
            "changes": [
                {
                    "characteristic_key": "non existent characteristic",
                    "delta": 10
                },
            ]
        }
        response = self.client.post(
            '/api/v1/organizations/1/repository/1/create/goal/',
            invalid_json,
            content_type='application/json',
        )

        self.assertEqual(
            response.status_code,
            400,
            (
                "It should return a 400 status code when the "
                "json contains an invalid characteristic key"
            ),
        )

    def test_if_the_final_goal_is_correct(self):
        valid_json = {
            "release_name": "v1.0.0",
            "start_at": "2022-08-19",
            "end_at": "2022-09-19",
            "changes": [
                {
                    "characteristic_key": "functional_suitability",
                    "delta": 10
                },
                {
                    "characteristic_key": "performance_efficiency",
                    "delta": -10
                },
                {
                    "characteristic_key": "security",
                    "delta": 40
                }
            ]
        }

        response = self.client.post(
            '/api/v1/organizations/1/repository/1/create/goal/',
            valid_json,
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()['data']

        expected_data = {
            "functional_suitability": 70,
            "performance_efficiency": 0,
            "security": 90,
        }

        self.assertEqual(
            data,
            expected_data,
            'Equalizer returned a different value than expected',
        )
