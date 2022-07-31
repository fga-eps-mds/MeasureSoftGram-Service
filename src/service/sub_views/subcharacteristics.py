from rest_framework import mixins, viewsets

from service import models, serializers


class SupportedSubCharacteristicModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna todas as subcaracterísticas suportadas pelo sistema
    """
    queryset = models.SupportedSubCharacteristic.objects.all()
    serializer_class = serializers.SupportedSubCharacteristicSerializer


class LatestCalculatedSubCharacteristicModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o último valor calculado da subcaracterística
    """
    queryset = models.SupportedSubCharacteristic.objects.prefetch_related('calculated_subcharacteristics')
    serializer_class = serializers.LatestCalculatedSubCharacteristicSerializer
