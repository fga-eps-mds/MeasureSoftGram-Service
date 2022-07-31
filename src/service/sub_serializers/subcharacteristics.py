from django.conf import settings
from rest_framework import serializers

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
