from django.conf import settings
from django.urls import reverse_lazy
from rest_framework import serializers

from metrics.models import CollectedMetric, SupportedMetric


class SupportedMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportedMetric
        fields = ('id', 'key', 'name', 'description')


class CollectedMetricSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para o endpoint que recebe métricas coletadas.
    """

    metric_id = serializers.IntegerField(source='metric.id')

    class Meta:
        model = CollectedMetric
        fields = (
            'id',
            'metric_id',
            'value',
            'created_at',
        )
        extra_kwargs = {
            'created_at': {"read_only": True},
        }

    def validate_metric_id(self, value):
        try:
            SupportedMetric.objects.get(id=value)

        except SupportedMetric.DoesNotExist as exc:
            raise serializers.ValidationError(
                f'There is no metric with the ID {value}.'
                'See the IDs of the metrics supported in the API in the '
                'endpoint: ' + reverse_lazy('service:supported-metrics-list')
            ) from exc

        return value

    def create(self, validated_data):
        metric_id = validated_data['metric']['id']
        metric = SupportedMetric.objects.get(id=metric_id)
        validated_data['metric'] = metric
        return super().create(validated_data)


class LatestCollectedMetricSerializer(serializers.ModelSerializer):
    """
    Serializadora que retorna o dado mais recente de uma determinada métrica.
    """

    latest = serializers.SerializerMethodField()

    class Meta:
        model = SupportedMetric
        fields = (
            'id',
            'key',
            'name',
            'description',
            'latest',
        )

    def get_latest(self, obj: SupportedMetric):
        try:
            latest = obj.collected_metrics.first()
            return CollectedMetricSerializer(latest).data
        except CollectedMetric.DoesNotExist:
            return None


class CollectedMetricHistorySerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField()

    class Meta:
        model = SupportedMetric
        fields = (
            'id',
            'key',
            'name',
            'description',
            'history',
        )

    def get_history(self, obj: SupportedMetric):
        MAX = settings.MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS
        try:
            # Os últimos MAX registros criados em ordem decrescente
            qs = obj.collected_metrics.all()[:MAX]
            return CollectedMetricSerializer(qs, many=True).data
        except SupportedMetric.DoesNotExist:
            return None
