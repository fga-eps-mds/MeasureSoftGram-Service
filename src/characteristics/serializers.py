from django.conf import settings
from rest_framework import serializers

import utils
from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic


class SupportedCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora para uma característica suportada
    """
    class Meta:
        model = SupportedCharacteristic
        fields = (
            'id',
            'key',
            'name',
            'description',
        )


class CalculatedCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as características calculadas
    """
    class Meta:
        model = CalculatedCharacteristic
        fields = (
            'id',
            'characteristic_id',
            'value',
            'created_at',
        )


class LatestCalculatedCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as características suportadas e seu último cálculo
    """

    latest = serializers.SerializerMethodField()

    class Meta:
        model = SupportedCharacteristic
        fields = (
            'id',
            'key',
            'name',
            'description',
            'latest',
        )

    def get_latest(self, obj: SupportedCharacteristic):
        try:
            latest = obj.calculated_characteristics.first()
            return CalculatedCharacteristicSerializer(latest).data
        except SupportedCharacteristic.DoesNotExist:
            return None


class CalculatedCharacteristicHistorySerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField()

    class Meta:
        model = SupportedCharacteristic
        fields = (
            'id',
            'key',
            'name',
            'description',
            'history',
        )

    def get_history(self, obj: SupportedCharacteristic):
        MAX = settings.MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS
        try:
            qs = obj.calculated_characteristics.all()[:MAX]
            return CalculatedCharacteristicSerializer(qs, many=True).data
        except CalculatedCharacteristic.DoesNotExist:
            return None


class CharacteristicsCalculationRequestSerializer(serializers.Serializer):
    """
    Serializadora usada para solicitar o cálculo de uma característica
    """
    key = serializers.CharField(max_length=255)


class CharacteristicsCalculationsRequestSerializer(serializers.Serializer):
    """
    Serializadora usada para solicitar o cálculo de várias características

    Aqui estou definindo uma lista de objetos pois é provável que no futuro
    outros parâmetros além de nome sejam necessários, e deste modo a evolução
    da API será somente a adição de novas chaves em
    CharacteristicsCalculationRequestSerializer
    """

    characteristics = serializers.ListField(
        child=CharacteristicsCalculationRequestSerializer(),
        required=True,
    )

    def validate(self, attrs):
        """
        Valida se todas as características solicitadas são suportadas
        """
        characteristics_keys = [
            char['key'] for char in attrs['characteristics']
        ]

        unsuported_chars: str = utils.validate_entity(
            characteristics_keys,
            SupportedCharacteristic.has_unsupported_characteristics
        )

        if unsuported_chars:
            raise serializers.ValidationError((
                "The following characteristics are "
                f"not supported: {unsuported_chars}"
            ))

        return attrs
