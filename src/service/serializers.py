from rest_framework import serializers

from service.models import Measure, Metric


class MetricModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = ('id', 'name', 'value', 'created_at')


class MeasureModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measure
        fields = ('id', 'name', 'value', 'created_at')
