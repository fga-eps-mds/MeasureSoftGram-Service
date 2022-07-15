import json
from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from service.models import Measure, Metric
from service.serializers import MeasureModelSerializer, MetricModelSerializer


class MetricModelView(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):

    queryset = Metric.objects.all()
    serializer_class = MetricModelSerializer


class MeasureModelView(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):

    queryset = Measure.objects.all()
    serializer_class = MeasureModelSerializer


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def import_sonar_metrics(request):
    data = dict(request.data)

    for metric_object in data['baseComponent']['measures']:
        print(metric_object['metric'])

    return Response()


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
def get_mocked_measures(request):
    return Response({
        'count': 5,
        'next': None,
        'previous': None,
        'results': [
            {
                'id': 1,
                'name': 'non_complex_file_density',
                'value': 0.45,
                'created_at': '2022-07-12T14:50:50.888777'
            },
            {
                'id': 2,
                'name': 'commented_file_density',
                'value': 0.69,
                'created_at': '2022-07-12T14:50:50.888777'
            },
            {
                'id': 3,
                'name': 'duplication_absense',
                'value': 0.8,
                'created_at': '2022-07-12T14:50:50.888777'
            },
            {
                'id': 4,
                'name': 'passed_tests',
                'value': 0.3,
                'created_at': '2022-07-12T14:50:50.888777'
            },
            {
                'id': 5,
                'name': 'test_builds',
                'value': 0.58,
                'created_at': '2022-07-12T14:50:50.888777'
            },
            {
                'id': 6,
                'name': 'test_coverage',
                'value': 0.92,
                'created_at': '2022-07-12T14:50:50.888777'
            },
        ]
    })
