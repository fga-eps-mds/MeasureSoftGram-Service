from rest_framework import serializers

from characteristics.serializers import CalculatedCharacteristicSerializer
from measures.serializers import CalculatedMeasureSerializer
from metrics.serializers import CollectedMetricSerializer
from subcharacteristics.serializers import \
    CalculatedSubCharacteristicSerializer
from tsqmi.serializers import TSQMISerializer


class GithubJSONSerializer(serializers.Serializer):
    metrics = serializers.DictField()


class SonarQubeJSONSerializer(serializers.Serializer):
    """
    Serializer for SonarQube JSON data.
    """

    paging = serializers.DictField()
    baseComponent = serializers.DictField()
    components = serializers.ListField()


class MetricsSerializer(serializers.Serializer):
    sonarqube = SonarQubeJSONSerializer()
    github = serializers.DictField()


class CalculateResponseSerializer(serializers.Serializer):
    tsqmi = TSQMISerializer
    metrics = CollectedMetricSerializer(many=True)
    measures = CalculatedMeasureSerializer(many=True)
    subcharacteristics = CalculatedSubCharacteristicSerializer(many=True)
    characteristics = CalculatedCharacteristicSerializer(many=True)
    tsqmi = TSQMISerializer()
