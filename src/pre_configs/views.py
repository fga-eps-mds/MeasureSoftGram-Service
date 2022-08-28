from rest_framework import mixins, status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from organizations.models import Product
from pre_configs.models import PreConfig
from pre_configs.serializers import PreConfigSerializer


class CurrentPreConfigModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    def list(self, request, *args, **kwargs):
        # first() == mais recente == pre configuração atual
        latest_pre_config = PreConfig.objects.first()
        serializer = PreConfigSerializer(latest_pre_config)
        return Response(serializer.data, status.HTTP_200_OK)


class CreatePreConfigModelViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PreConfigSerializer

    def perform_create(self, serializer):
        product = get_object_or_404(
            Product,
            id=self.kwargs['product_pk'],
        )
        serializer.save(product=product)
