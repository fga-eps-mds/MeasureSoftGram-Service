from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from service import staticfiles


@api_view(['GET', 'HEAD', 'OPTIONS'])
def get_mocked_repository(request):
    return Response({
        'id': 1,
        'name': '2022-1-MeasureSoftGram-Front',
        'description': 'Repositório Frontend do software MeasureSoftGram.',
        'github_url': 'https://github.com/fga-eps-mds/2022-1-MeasureSoftGram-Front',
        'created_at': '2022-07-14T020:00:55.603466',
        'updated_at': '2022-07-15T08:58:55.603466'
    })


@api_view(['GET', 'HEAD', 'OPTIONS'])
def get_mocked_measures_history(request):
    return Response(staticfiles.MOCKED_MEASURE_HISTORY)


@api_view(['GET', 'HEAD', 'OPTIONS'])
def get_mocked_measures(request):
    return Response({
        "count": 100,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": 1,
                "key": "passed_tests",
                "name": "Passed tests",
                "description": "",
                "latest_collected_measure": {
                    "id": 10003,
                    "measure_id": 1,
                    "value": 0.5,
                    "created_at": "2022-07-16T14:45:25-03:00"
                }
            },
            {
                "id": 2,
                "key": "fast_test_builds",
                "name": "Fast test builds",
                "description": "Fast test builds",
                "latest_collected_measure": {
                    "id": 10004,
                    "measure_id": 2,
                    "value": 0.3,
                    "created_at": "2022-07-16T15:22:21-03:00"
                }
            },
            {
                "id": 3,
                "key": "test_coverage",
                "name": "Test coverage",
                "description": "",
                "latest_collected_measure": {
                    "id": 3969,
                    "measure_id": 3,
                    "value": 0.68,
                    "created_at": "2022-07-16T12:49:37-03:00"
                }
            },
            {
                "id": 4,
                "key": "non_complex_files_density",
                "name": "Non complex files density",
                "description": "",
                "latest_collected_measure": {
                    "id": 4981,
                    "measure_id": 4,
                    "value": 0.42,
                    "created_at": "2022-07-15T12:00:15-03:00"
                }
            },
            {
                "id": 5,
                "key": "commented_files_density",
                "name": "Commented files density",
                "description": "",
                "latest_collected_measure": {
                    "id": 4367,
                    "measure_id": 5,
                    "value": 0.26,
                    "created_at": "2022-07-16T02:13:37-03:00"
                }
            },
            {
                "id": 6,
                "key": "absence_of_duplications",
                "name": "Absence of duplications",
                "description": "",
                "latest_collected_measure": {
                    "id": 4367,
                    "measure_id": 6,
                    "value": 0.62,
                    "created_at": "2022-07-16T02:13:37-03:00"
                }
            },
        ]
    })


@api_view(['GET', 'HEAD', 'OPTIONS'])
def get_specific_mocked_measure(request, measure_id):
    mocked_data = {
        1: {
            "id": 1,
            "key": "passed_tests",
            "name": "Passed tests",
            "description": "",
            "latest_collected_measure": {
                "id": 10003,
                "measure_id": 1,
                "value": 0.5,
                "created_at": "2022-07-16T14:45:25-03:00"
            }
        },
        2: {
            "id": 2,
            "key": "fast_test_builds",
            "name": "Fast test builds",
            "description": "Fast test builds",
            "latest_collected_measure": {
                "id": 10004,
                "measure_id": 2,
                "value": 0.3,
                "created_at": "2022-07-16T15:22:21-03:00"
            }
        },
        3: {
            "id": 3,
            "key": "test_coverage",
            "name": "Test coverage",
            "description": "",
            "latest_collected_measure": {
                "id": 3969,
                "measure_id": 3,
                "value": 0.68,
                "created_at": "2022-07-16T12:49:37-03:00"
            }
        },
        4: {
            "id": 4,
            "key": "non_complex_files_density",
            "name": "Non complex files density",
            "description": "",
            "latest_collected_measure": {
                "id": 4981,
                "measure_id": 4,
                "value": 0.42,
                "created_at": "2022-07-15T12:00:15-03:00"
            }
        },
        5: {
            "id": 5,
            "key": "commented_files_density",
            "name": "Commented files density",
            "description": "",
            "latest_collected_measure": {
                "id": 4367,
                "measure_id": 5,
                "value": 0.26,
                "created_at": "2022-07-16T02:13:37-03:00"
            }
        },
        6: {
            "id": 6,
            "key": "absence_of_duplications",
            "name": "Absence of duplications",
            "description": "",
            "latest_collected_measure": {
                "id": 4367,
                "measure_id": 6,
                "value": 0.62,
                "created_at": "2022-07-16T02:13:37-03:00"
            }
        },
    }
    if measure_id not in mocked_data:
        return Response(
            data={"detail": "Not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    return Response(mocked_data[measure_id], status=status.HTTP_200_OK)
