
from rest_framework import serializers

from service import models
from service import serializers as service_serializers


class CharacteristicEntityRelationshipTreeSerializer(
    serializers.ModelSerializer,
):
    """
    Serializer para a árvore de relacionamentos entre as entidades
    """

    subcharacteristics = serializers.SerializerMethodField()

    class Meta:
        model = models.SupportedCharacteristic
        fields = (
            'id',
            'name',
            'key',
            'description',
            'subcharacteristics',
        )

    def get_subcharacteristics(self, obj: models.SupportedCharacteristic):
        return SubCharacteristicEntityRelationshipTreeSerializer(
            obj.subcharacteristics.all(),
            many=True,
        ).data


class SubCharacteristicEntityRelationshipTreeSerializer(
    serializers.ModelSerializer,
):
    measures = serializers.SerializerMethodField()

    class Meta:
        model = models.SupportedCharacteristic
        fields = (
            'id',
            'name',
            'key',
            'description',
            'measures',
        )

    def get_measures(self, obj: models.SupportedCharacteristic):
        return service_serializers.SupportedMeasureSerializer(
            obj.measures.all(),
            many=True,
        ).data
