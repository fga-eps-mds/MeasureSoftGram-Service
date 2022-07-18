from rest_framework import mixins, viewsets

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
