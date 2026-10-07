from rest_framework import mixins, viewsets

from organizations.mixins import UserScopedMixin
from subcharacteristics.models import SupportedSubCharacteristic
from subcharacteristics.serializers import (
    CalculatedSubCharacteristicHistorySerializer,
    LatestCalculatedSubCharacteristicSerializer,
    SupportedSubCharacteristicSerializer,
)


class SupportedSubCharacteristicModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna todas as subcaracterísticas suportadas pelo sistema
    """

    queryset = SupportedSubCharacteristic.objects.all()
    serializer_class = SupportedSubCharacteristicSerializer


class RepositorySubCharacteristicMixin(UserScopedMixin):
    def get_queryset(self):
        repository = self.get_repository()
        qs = repository.calculated_subcharacteristics.all()
        qs = qs.values_list("subcharacteristic", flat=True).distinct()
        return SupportedSubCharacteristic.objects.filter(id__in=qs)


class LatestCalculatedSubCharacteristicModelViewSet(
    RepositorySubCharacteristicMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o último valor calculado da subcaracterística
    """

    queryset = SupportedSubCharacteristic.objects.prefetch_related(
        "calculated_subcharacteristics",
    )
    serializer_class = LatestCalculatedSubCharacteristicSerializer


class CalculatedSubCharacteristicHistoryModelViewSet(
    RepositorySubCharacteristicMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o histórico de subcaracterísticas calculadas
    """

    queryset = SupportedSubCharacteristic.objects.prefetch_related(
        "calculated_subcharacteristics",
    )
    serializer_class = CalculatedSubCharacteristicHistorySerializer
