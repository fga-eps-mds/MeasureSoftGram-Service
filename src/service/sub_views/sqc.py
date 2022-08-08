from rest_framework import mixins, status, viewsets

from service import models, serializers


class SQCModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para cadastrar as medidas coletadas
    """
    queryset = models.SQC.objects.all()
    serializer_class = serializers.SQCSerializer
