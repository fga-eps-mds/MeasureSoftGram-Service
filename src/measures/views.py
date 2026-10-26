from rest_framework import mixins, viewsets

from measures.models import SupportedMeasure
from measures.serializers import (
    CalculatedMeasureHistorySerializer,
    LatestMeasuresCalculationsRequestSerializer,
    SupportedMeasureSerializer,
)
from organizations.mixins import UserScopedMixin


class SupportedMeasureModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna todas as medidas suportadas pelo sistema
    """

    queryset = SupportedMeasure.objects.all()
    serializer_class = SupportedMeasureSerializer


class RepositoryMeasuresMixin(UserScopedMixin):
    def get_queryset(self):
        repository = self.get_repository()
        qs = repository.calculated_measures.all()
        qs = qs.values_list("measure", flat=True).distinct()
        # sem prefetch de calculated_measures: os serializers filtram pelo repositório, e o prefetch
        # carregava as medidas calculadas de todos os repositórios só para descartá-las
        return SupportedMeasure.objects.filter(id__in=qs)


class LatestCalculatedMeasureModelViewSet(
    RepositoryMeasuresMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para cadastrar as medidas coletadas
    """

    queryset = SupportedMeasure.objects.prefetch_related(
        "calculated_measures",
    )
    serializer_class = LatestMeasuresCalculationsRequestSerializer


class CalculatedMeasureHistoryModelViewSet(
    RepositoryMeasuresMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para ler o histórico de medidas coletadas
    TODO: Criar uma classe de paginação (
        https://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style
    )
    """

    queryset = SupportedMeasure.objects.prefetch_related(
        "calculated_measures",
    )
    serializer_class = CalculatedMeasureHistorySerializer
