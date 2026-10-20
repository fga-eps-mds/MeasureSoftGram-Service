from django.conf import settings
from rest_framework import serializers

import utils
from measures.models import CalculatedMeasure, SupportedMeasure


class SupportedMeasureSerializer(serializers.ModelSerializer):
    """
    Serializadora para uma medida suportada
    """

    class Meta:
        model = SupportedMeasure
        fields = (
            "id",
            "key",
            "name",
            "description",
        )


class CalculatedMeasureSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as medidas calculadas
    """

    class Meta:
        model = CalculatedMeasure
        fields = (
            "id",
            "measure_id",
            "value",
            "created_at",
        )


class LatestMeasuresCalculationsRequestSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as medidas suportadas
    e seu último cálculo
    """

    latest = serializers.SerializerMethodField()

    class Meta:
        model = SupportedMeasure
        fields = (
            "id",
            "key",
            "name",
            "description",
            "latest",
        )

    def get_latest(self, obj: SupportedMeasure):
        try:
            repository = self.context["view"].get_repository()

            latest = obj.calculated_measures.filter(repository=repository).first()

            return CalculatedMeasureSerializer(latest).data
        except CalculatedMeasure.DoesNotExist:
            return None


class CalculatedMeasureHistorySerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField()

    class Meta:
        model = SupportedMeasure
        fields = (
            "id",
            "key",
            "name",
            "description",
            "history",
        )

    def get_history(self, obj: SupportedMeasure):
        MAX = settings.MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS
        try:
            qs = obj.calculated_measures.all()

            repository = self.context["view"].get_repository()
            qs = qs.filter(repository=repository)

            return CalculatedMeasureSerializer(utils.get_latest_history(qs, MAX), many=True).data
        except CalculatedMeasure.DoesNotExist:
            return None
