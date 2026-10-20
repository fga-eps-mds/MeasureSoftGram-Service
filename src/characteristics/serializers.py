from django.conf import settings
from rest_framework import serializers

import utils
from characteristics.models import BalanceMatrix, CalculatedCharacteristic, SupportedCharacteristic


class SupportedCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora para uma característica suportada
    """

    class Meta:
        model = SupportedCharacteristic
        fields = (
            "id",
            "key",
            "name",
            "description",
        )


class BalanceMatrixSerializer(serializers.ModelSerializer):
    """
    Serializadora para a matriz de balanceamento
    """

    source_characteristic = SupportedCharacteristicSerializer()
    target_characteristic = SupportedCharacteristicSerializer()

    class Meta:
        model = BalanceMatrix
        fields = (
            "id",
            "source_characteristic",
            "target_characteristic",
            "relation_type",
        )

        extra_kwargs = {
            "key": {"read_only": True},
        }


class CalculatedCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as características calculadas
    """

    class Meta:
        model = CalculatedCharacteristic
        fields = (
            "id",
            "characteristic_id",
            "value",
            "created_at",
        )


class LatestCalculatedCharacteristicSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as características suportadas e seu último cálculo
    """

    latest = serializers.SerializerMethodField()

    class Meta:
        model = SupportedCharacteristic
        fields = (
            "id",
            "key",
            "name",
            "description",
            "latest",
        )

    def get_latest(self, obj: SupportedCharacteristic):
        try:
            repository = self.context["view"].get_repository()

            latest = obj.calculated_characteristics.filter(repository=repository).first()

            return CalculatedCharacteristicSerializer(latest).data
        except SupportedCharacteristic.DoesNotExist:
            return None


class CalculatedCharacteristicHistorySerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField()

    class Meta:
        model = SupportedCharacteristic
        fields = (
            "id",
            "key",
            "name",
            "description",
            "history",
        )

    def get_history(self, obj: SupportedCharacteristic):
        MAX = settings.MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS

        try:
            qs = obj.calculated_characteristics.all()

            repository = self.context["view"].get_repository()
            qs = qs.filter(repository=repository)

            return CalculatedCharacteristicSerializer(
                utils.get_latest_history(qs, MAX),
                many=True,
            ).data

        except CalculatedCharacteristic.DoesNotExist:
            return None
