from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def get_mocked_repository(request):
    return Response({
        'id': 1,
        'name': '2022-1-MeasureSoftGram-Front',
        'description': 'Repositório Frontend do software MeasureSoftGram.',
        'github_url': 'https://github.com/fga-eps-mds/2022-1-MeasureSoftGram-Front',
        'created_at': '2022-07-14T020:00:55.603466',
        'updated_at': '2022-07-15T08:58:55.603466'
    })
