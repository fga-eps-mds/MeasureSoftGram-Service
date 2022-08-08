from django.conf import settings
from rest_framework import serializers

import utils
from service import models


class SupportedSubCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora para uma subcaracterística suportada
    """
    class Meta:
        model = models.SupportedSubCharacteristic
        fields = (
            'id',
            'key',
            'name',
            'description',
        )


class CalculatedSubCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as subcaracterísticas calculadas
    """
    class Meta:
        model = models.CalculatedSubCharacteristic
        fields = (
            'id',
            'subcharacteristic',
            'value',
            'created_at',
        )


class LatestCalculatedSubCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as subcaracterísticas suportadas e seu último cálculo
    """

    latest = serializers.SerializerMethodField()

    class Meta:
        model = models.SupportedSubCharacteristic
        fields = (
            'id',
            'key',
            'name',
            'description',
            'latest',
        )

    def get_latest(self, obj: models.SupportedSubCharacteristic):
        try:
            latest = obj.calculated_subcharacteristics.first()
            return CalculatedSubCharacteristicSerializer(latest).data
        except models.SupportedSubCharacteristic.DoesNotExist:
            return None


class CalculatedSubCharacteristicHistorySerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField()

    class Meta:
        model = models.SupportedSubCharacteristic
        fields = (
            'id',
            'key',
            'name',
            'description',
            'history',
        )

    def get_history(self, obj: models.SupportedSubCharacteristic):
        MAX = settings.MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS
        try:
            qs = obj.calculated_subcharacteristics.all()[:MAX]
            return CalculatedSubCharacteristicSerializer(qs, many=True).data
        except models.CalculatedSubCharacteristic.DoesNotExist:
            return None


class SubcharacteristicsCalculationRequestSerializer(serializers.Serializer):
    """
    Serializadora usada para solicitar o cálculo de uma subcaracterística
    """
    key = serializers.CharField(max_length=255)


class SubcharacteristicsCalculationsRequestSerializer(
    serializers.Serializer
):
    """
    Serializadora usada para solicitar o cálculo de várias subcaracterísticas

    Aqui estou definindo uma lista de objetos pois é provável que no futuro
    outros parâmetros além de nome sejam necessários, e deste modo a evolução
    da API será somente a adição de novas chaves em
    SubcharacteristicsCalculationRequestSerializer
    """
    subcharacteristics = serializers.ListField(
        child=SubcharacteristicsCalculationRequestSerializer(),
        required=True,
    )

    def validate(self, attrs):
        """
        Valida se todas as subcaracterísticas solicitadas são suportadas
        """
        subcharacteristics_keys = [
            subchar['key'] for subchar in attrs['subcharacteristics']
        ]

        unsuported_subchars: str = utils.validate_entity(
            subcharacteristics_keys,
            models.SupportedSubCharacteristic.has_unsupported_subcharacteristics
        )

        if unsuported_subchars:
            raise serializers.ValidationError((
                "The following subcharacteristics are "
                f"not supported: {unsuported_subchars}"
            ))

        return attrs
