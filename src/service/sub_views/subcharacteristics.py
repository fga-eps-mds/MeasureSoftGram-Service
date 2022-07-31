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
