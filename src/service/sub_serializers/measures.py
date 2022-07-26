from rest_framework import serializers

from service import models


class SupportedMeasureSerializer(serializers.ModelSerializer):
    """
    Serializadora para uma medida suportada
    """
    class Meta:
        model = models.SupportedMeasure
        fields = (
            'id',
            'key',
            'name',
            'description',
        )


class MeasureCalculationRequestSerializer(serializers.Serializer):
    """
    Serializadora usada para solicitar o cálculo de uma medida
    """
    key = serializers.CharField(max_length=255)


class MeasuresCalculationsRequestSerializer(serializers.Serializer):
    """
    Serializadora usada para solicitar o cálculo de várias medidas

    Aqui estou definindo uma lista de objetos pois é provável que no futuro
    outros parâmetros além de nome sejam necessários, e deste modo a evolução
    da API será somente a adição de novas chaves em MeasureCalculationRequestSerializer
    """
    measures = serializers.ListField(
        child=MeasureCalculationRequestSerializer(),
        required=True,
    )

    def validate(self, attrs):
        """
        Valida se todas as medidas solicitadas são suportadas
        """
        measure_keys = [
            measure['key']
            for measure in attrs['measures']
        ]

        qs = models.SupportedMeasure.objects.filter(
            key__in=measure_keys,
        )

        supported_measures_keys = [
            measure.key for measure in qs
        ]

        supported_measures_set = set(supported_measures_keys)
        measure_keys_set = set(measure_keys)

        if unsuported_measures := measure_keys_set - supported_measures_set:
            unsuported_measures = [
                f"`{key}`"
                for key in unsuported_measures
            ]

            unsuported_measures = ', '.join(unsuported_measures)

            raise serializers.ValidationError((
                "The following measures "
                f"are not supported: {unsuported_measures}"
            ))

        return attrs


class CalculatedMeasureSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as medidas calculadas
    """
    class Meta:
        model = models.CalculatedMeasure
        fields = (
            'id',
            'measure',
            'value',
            'created_at',
        )


class LatestMeasuresCalculationsRequestSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar as medidas suportadas
    e seu último cálculo
    """

    latest = serializers.SerializerMethodField()

    class Meta:
        model = models.SupportedMeasure
        fields = (
            'id',
            'key',
            'name',
            'description',
            'latest',
        )

    def get_latest(self, obj: models.SupportedMeasure):
        try:
            latest = obj.calculated_measures.first()
            return CalculatedMeasureSerializer(latest).data
        except models.CollectedMetric.DoesNotExist:
            return None


class CalculatedMeasureHistorySerializer(serializers.ModelSerializer):
    # history = CalculatedMeasureSerializer(
    #     source='calculated_measures',
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
        try:
            # Os últimos 10 registros criados em ordem decrescente
            qs = obj.calculated_measures.all()[:25]
            return CalculatedMeasureSerializer(qs, many=True).data
        except models.CalculatedMeasure.DoesNotExist:
            return None
