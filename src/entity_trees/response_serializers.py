"""Schema OpenAPI da árvore que `build_quality_model_tree` monta (só documentação)."""

from rest_framework import serializers


class _NodeSerializer(serializers.Serializer):
    """`_entity_node`: sem a entidade suportada no banco, `id` e `description` vêm `null`."""

    id = serializers.IntegerField(allow_null=True)
    type = serializers.CharField()
    key = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True, allow_blank=True)
    weight = serializers.FloatField(allow_null=True)


class QualityModelMetricNodeSerializer(_NodeSerializer):
    children = serializers.ListField(child=serializers.DictField(), max_length=0)


class QualityModelMeasureNodeSerializer(_NodeSerializer):
    min_threshold = serializers.FloatField(allow_null=True)
    max_threshold = serializers.FloatField(allow_null=True)
    children = QualityModelMetricNodeSerializer(many=True)


class QualityModelSubcharacteristicNodeSerializer(_NodeSerializer):
    children = QualityModelMeasureNodeSerializer(many=True)


class QualityModelCharacteristicNodeSerializer(_NodeSerializer):
    children = QualityModelSubcharacteristicNodeSerializer(many=True)


class QualityModelTreeSerializer(_NodeSerializer):
    """A raiz (TSQMI). A lista vem vazia sem configuração."""

    children = QualityModelCharacteristicNodeSerializer(many=True)
