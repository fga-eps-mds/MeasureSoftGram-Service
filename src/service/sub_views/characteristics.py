from rest_framework import mixins, viewsets

from service import models, serializers


class SupportedCharacteristicModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna todas as características suportadas pelo sistema
    """
    queryset = models.SupportedCharacteristic.objects.all()
    serializer_class = serializers.SupportedCharacteristicSerializer


class LatestCalculatedCharacteristicModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o último valor calculado da característica
    """
    queryset = models.SupportedCharacteristic.objects.prefetch_related(
        'calculated_characteristics'
    )
    serializer_class = serializers.LatestCalculatedCharacteristicSerializer


class CalculatedCharacteristicHistoryModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o histórico de características calculadas
    """
    queryset = models.SupportedCharacteristic.objects.prefetch_related(
        'calculated_characteristics'
    )
    serializer_class = serializers.CalculatedCharacteristicHistorySerializer
