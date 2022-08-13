from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from service import models, serializers


class CurrentPreConfigModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    def list(self, request, *args, **kwargs):
        # first() == mais recente == pre configuração atual
        latest_pre_config = models.PreConfig.objects.first()
        serializer = serializers.PreConfigSerializer(latest_pre_config)
        return Response(serializer.data, status.HTTP_200_OK)


class CreatePreConfigModelViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.PreConfigSerializer
