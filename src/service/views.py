from django.db.models import Prefetch

from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from service import models, serializers


class SupportedMetricModelViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Viewset que retorna todas as métricas suportadas pelo sistema
    """
    queryset = models.SupportedMetric.objects.all()
    serializer_class = serializers.SupportedMetricSerializer


class CollectedMetricModelViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para cadastrar as métricas coletadas
    """
    queryset = models.CollectedMetric.objects.all()
    serializer_class = serializers.CollectedMetricSerializer


class LatestCollectedMetricModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para ler o valor mais recente das métricas coletadas
    """

    # TODO: Melhorar essa query
    # O desejável era que somente fosse realizado o prefetch no último CollectedMetric de cada foreinkey
    queryset = models.SupportedMetric.objects.prefetch_related('collected_metrics')

    # O Código abaixo é a forma como o django permite fazer um prefetch customizado, mas não está funcinando
    # queryset = models.SupportedMetric.objects.prefetch_related(
    #     Prefetch(
    #         'collected_metrics',
    #         queryset=models.CollectedMetric.objects.filter(
    #             pk=models.CollectedMetric.objects.latest('id').pk,
    #         ),
    #     )
    # )

    serializer_class = serializers.LatestCollectedMetricSerializer


class CollectedMetricHistoryModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para ler o histórico de métricas coletadas

    TODO: Limitar o número de métricas durante a solicitação do histórico
    TODO: Criar uma classe de paginação (
        https://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style
    )
    """
    queryset = models.SupportedMetric.objects.prefetch_related(
        'collected_metrics'
    )
    serializer_class = serializers.CollectedMetricHistorySerializer


# class MeasureModelView(mixins.ListModelMixin, viewsets.GenericViewSet):
#     """
#     ModelViewSet para listar os valores das medidas
#     calculadas pelas fórmulas do modelo.
#     """
#     queryset = Measure.objects.all()
#     serializer_class = MeasureModelSerializer


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def import_sonar_metrics(request):
    """
    Endpoint que recebe um o JSON obtido na API do SonarQube,
    extrai os valores das métricas contidas e salva no banco de dados.
    """

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
