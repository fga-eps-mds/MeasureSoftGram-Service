from django.conf import settings
from rest_framework import serializers

from service import models


class SupportedCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora para uma característica suportada
    """
    class Meta:
        model = models.SupportedCharacteristic
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
        model = models.CalculatedCharacteristic
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
        model = models.SupportedCharacteristic
        fields = (
            'id',
            'key',
            'name',
            'description',
            'latest',
        )

    def get_latest(self, obj: models.SupportedCharacteristic):
        try:
            latest = obj.calculated_characteristics.first()
            return CalculatedCharacteristicSerializer(latest).data
        except models.SupportedCharacteristic.DoesNotExist:
            return None


class CalculatedCharacteristicHistorySerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField()

    class Meta:
        model = models.SupportedCharacteristic
        fields = (
            'id',
            'key',
            'name',
            'description',
            'history',
        )

    def get_history(self, obj: models.SupportedCharacteristic):
        MAX = settings.MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS
        try:
            qs = obj.calculated_characteristics.all()[:MAX]
            return CalculatedCharacteristicSerializer(qs, many=True).data
        except models.CalculatedCharacteristic.DoesNotExist:
            return None
