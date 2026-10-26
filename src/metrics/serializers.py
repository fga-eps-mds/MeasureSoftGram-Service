from django.conf import settings
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from rest_framework import serializers

import utils
from metrics.models import CollectedMetric, SupportedMetric


class SupportedMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportedMetric
        fields = ("id", "key", "name", "description")


class CollectedMetricSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para o endpoint que recebe métricas coletadas.
    """

    metric_id = serializers.IntegerField(source="metric.id")

    class Meta:
        model = CollectedMetric
        fields = (
            "id",
            "metric_id",
            "value",
            "created_at",
        )
        extra_kwargs = {
            "created_at": {"read_only": True},
        }

    def validate_metric_id(self, value):
        try:
            SupportedMetric.objects.get(id=value)

        except SupportedMetric.DoesNotExist as exc:
            raise serializers.ValidationError(
                f"There is no metric with the ID {value}."
                "See the IDs of the metrics supported in the API in the "
                "endpoint: " + reverse_lazy("service:supported-metrics-list")
            ) from exc

        return value

    def create(self, validated_data):
        metric_id = validated_data["metric"]["id"]
        metric = SupportedMetric.objects.get(id=metric_id)
        validated_data["metric"] = metric
        return super().create(validated_data)


class LatestCollectedMetricSerializer(utils.RepositoryRecordsMixin, serializers.ModelSerializer):
    """
    Serializadora que retorna o dado mais recente de uma determinada métrica.
    """

    records_model = CollectedMetric
    entity_field = "metric_id"
    latest = serializers.SerializerMethodField()

    class Meta:
        model = SupportedMetric
        fields = (
            "id",
            "key",
            "name",
            "description",
            "latest",
        )

    def get_records_queryset(self):
        qs = super().get_records_queryset()
        # sem qualifier, o último registro da coleta pode ser o de um arquivo; qualifier=TRK traz o do repositório
        qualifier = self.context.get("qualifier")
        return qs.filter(qualifier=qualifier) if qualifier else qs

    def get_latest(self, obj: SupportedMetric):
        return CollectedMetricSerializer(self.get_entity_latest(obj)).data


class CollectedMetricHistorySerializer(utils.RepositoryRecordsMixin, serializers.ModelSerializer):
    records_model = CollectedMetric
    entity_field = "metric_id"
    history = serializers.SerializerMethodField()

    class Meta:
        model = SupportedMetric
        fields = (
            "id",
            "key",
            "name",
            "description",
            "history",
        )

    def get_records_queryset(self):
        start_at = self.context.get("start_at")
        end_at = self.context.get("end_at")
        qualifier = self.context.get("qualifier")

        # Parse dates
        start_date = parse_date(start_at) if start_at else None
        end_date = parse_date(end_at) if end_at else None

        qs = super().get_records_queryset()
        # qualifier=TRK deixa só o valor do repositório, sem os valores por arquivo
        if qualifier:
            qs = qs.filter(qualifier=qualifier)
        if start_date:
            qs = qs.filter(created_at__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__lte=end_date)
        return qs

    def get_history(self, obj: SupportedMetric):
        MAX = settings.MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS
        return CollectedMetricSerializer(self.get_entity_records(obj, MAX), many=True).data
