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


class LatestMeasuresCalculationsRequestSerializer(utils.RepositoryRecordsMixin, serializers.ModelSerializer):
    """
    Serializadora usada para serializar as medidas suportadas
    e seu último cálculo
    """

    records_model = CalculatedMeasure
    entity_field = "measure_id"
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
        return CalculatedMeasureSerializer(self.get_entity_latest(obj)).data


class CalculatedMeasureHistorySerializer(utils.RepositoryRecordsMixin, serializers.ModelSerializer):
    records_model = CalculatedMeasure
    entity_field = "measure_id"
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
        return CalculatedMeasureSerializer(self.get_entity_records(obj, MAX), many=True).data
