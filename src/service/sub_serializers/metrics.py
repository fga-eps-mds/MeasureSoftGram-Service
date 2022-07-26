from django.conf import settings
from django.urls import reverse_lazy
from rest_framework import serializers

from service import models


class SupportedMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SupportedMetric
        fields = ('id', 'key', 'name', 'description')


class CollectedMetricSerializer(serializers.ModelSerializer):
    metric_id = serializers.IntegerField(source='metric.id')

    class Meta:
        model = models.CollectedMetric
        fields = (
            'id',
            'metric_id',
            'value',
            'created_at',
        )

    def validate_metric_id(self, value):
        try:
            models.SupportedMetric.objects.get(id=value)

        except models.SupportedMetric.DoesNotExist as exc:
            raise serializers.ValidationError(
                f'There is no metric with the ID {value}.'
                'See the IDs of the metrics supported in the API in the '
                'endpoint: ' + reverse_lazy('service:supported-metrics-list')
            ) from exc

        return value

    def create(self, validated_data):
        metric_id = validated_data['metric']['id']
        metric = models.SupportedMetric.objects.get(id=metric_id)
        validated_data['metric'] = metric
        return super().create(validated_data)


class LatestCollectedMetricSerializer(serializers.ModelSerializer):

    latest = serializers.SerializerMethodField()

    class Meta:
        model = models.SupportedMetric
        fields = (
            'id',
            'key',
            'name',
            'description',
            'latest',
        )

    def get_latest(self, obj: models.SupportedMetric):
        try:
            latest = obj.collected_metrics.first()
            return CollectedMetricSerializer(latest).data
        except models.CollectedMetric.DoesNotExist:
            return None


class CollectedMetricHistorySerializer(serializers.ModelSerializer):
    # history = CollectedMetricSerializer(
    #     source='collected_metrics',
    #     many=True,
    # )
    history = serializers.SerializerMethodField()

    class Meta:
        model = models.SupportedMetric
        fields = (
            'id',
            'key',
            'name',
            'description',
            'history',
        )

    def get_history(self, obj: models.SupportedMeasure):
        MAX = settings.MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS
        try:
            # Os últimos 10 registros criados em ordem decrescente
            qs = obj.collected_metrics.all()[:MAX]
            return CollectedMetricSerializer(qs, many=True).data
        except models.CalculatedMeasure.DoesNotExist:
            return None
