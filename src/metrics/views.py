from rest_framework import mixins, viewsets
from rest_framework.generics import get_object_or_404

from metrics.models import CollectedMetric, SupportedMetric
from metrics.serializers import (
    CollectedMetricHistorySerializer,
    CollectedMetricSerializer,
    LatestCollectedMetricSerializer,
    SupportedMetricSerializer,
)
from organizations.models import Repository


class SupportedMetricModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna todas as métricas suportadas pelo sistema
    """
    queryset = SupportedMetric.objects.all()
    serializer_class = SupportedMetricSerializer


class CollectedMetricModelViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para cadastrar as métricas coletadas
    """
    queryset = CollectedMetric.objects.all()
    serializer_class = CollectedMetricSerializer

    def perform_create(self, serializer):
        repository = get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
        )
        serializer.save(repository=repository)


class LatestCollectedMetricModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para ler o valor mais recente das métricas coletadas
    """

    # TODO: Melhorar essa query
    # O desejável era que somente fosse realizado o
    # prefetch no último CollectedMetric de cada foreinkey
    queryset = SupportedMetric.objects.prefetch_related('collected_metrics')

    # O Código abaixo é a forma como o django permite fazer
    # um prefetch customizado, mas não está funcinando
    # queryset = SupportedMetric.objects.prefetch_related(
    #     Prefetch(
    #         'collected_metrics',
    #         queryset=CollectedMetric.objects.filter(
    #             pk=CollectedMetric.objects.latest('id').pk,
    #         ),
    #     )
    # )

    serializer_class = LatestCollectedMetricSerializer


class CollectedMetricHistoryModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para ler o histórico de métricas coletadas

    TODO: Criar uma classe de paginação (
        https://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style
    )
    """
    queryset = SupportedMetric.objects.prefetch_related(
        'collected_metrics',
    )
    serializer_class = CollectedMetricHistorySerializer
