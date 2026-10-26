"""
Módulo que agrupa as views relacionadas à árvore de entidades. Quando dizemos
árvore de entidades, estamos falando do relacionamentos entre as entidades.
Isso é:
* Características com subcaracterísticas
* Subcaracterísticas com medidas
"""

from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from characteristics.models import SupportedCharacteristic
from entity_trees.serializers import CharacteristicEntityRelationshipTreeSerializer, pre_config_to_entity_tree
from entity_trees.services import build_quality_model_tree, resolve_release_configuration
from organizations.mixins import UserScopedMixin
from releases.models import Release


class SupportedEntitiesRelationshipTreeViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet as entidades suportadas e suas relações no formato de árvore
    """

    serializer_class = CharacteristicEntityRelationshipTreeSerializer
    queryset = SupportedCharacteristic.objects.all()

    def list(self, request, *args, **kwargs):
        qs = SupportedCharacteristic.objects.all().prefetch_related(
            "subcharacteristics",
            "subcharacteristics__measures",
        )

        serializer = CharacteristicEntityRelationshipTreeSerializer(
            qs,
            many=True,
        )

        return Response(serializer.data)


class ReleaseConfigurationEntitiesRelationshipTreeViewSet(
    UserScopedMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna as entidades de uma pré-configução e
    suas relações no formato de árvore
    """

    serializer_class = CharacteristicEntityRelationshipTreeSerializer
    queryset = SupportedCharacteristic.objects.all()

    def list(self, request, *args, **kwargs):
        product = self.get_product()
        current_pre_config = product.release_configuration.first()
        entity_tree = pre_config_to_entity_tree(current_pre_config)
        return Response(entity_tree)


class QualityModelTreeViewSet(
    UserScopedMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet que retorna a árvore do modelo de qualidade de uma release
    (ou da configuração atual, caso release_id não seja informado).
    """

    def list(self, request, *args, **kwargs):
        product = self.get_product()

        release_id_param = request.query_params.get("release_id")
        release = None

        if release_id_param is not None:
            try:
                release_id = int(release_id_param)
            except (ValueError, TypeError):
                return Response(
                    {"detail": "O parâmetro release_id deve ser um número inteiro válido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            release = Release.objects.filter(product=product, id=release_id).first()
            if not release:
                return Response(
                    {"detail": "Release não encontrada para este produto."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        config = resolve_release_configuration(product, release=release)
        tree = build_quality_model_tree(config)
        return Response(tree, status=status.HTTP_200_OK)
