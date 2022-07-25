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
            latest = obj.collected_metrics.last()
            return CollectedMetricSerializer(latest).data
        except models.CollectedMetric.DoesNotExist:
            return None


class CollectedMetricHistorySerializer(serializers.ModelSerializer):
    collected_metric_history = CollectedMetricSerializer(
        source='collected_metrics',
        many=True,
    )

    class Meta:
        model = models.SupportedMetric
        fields = (
            'id',
            'key',
            'name',
            'description',
            'collected_metric_history',
        )
