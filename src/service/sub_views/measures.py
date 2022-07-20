from rest_framework.response import Response

from service import models
from service import clients
from service import serializers


def calculate_measure(request, measure_id):
    """
    Calculate a measure for a specific repository.
    """
    # Validatar se essa medida existe

    # Obter a instância da medida no banco de dados
    measure = models.SupportedMeasure.objects.get(id=measure_id)

    # Obter as métricas necessárias para calcular a medida
    metric1 = models.SupportedMetric.objects.get(key='key_name_1')
    metric2 = models.SupportedMetric.objects.get(key='key_name_2')
    metric3 = models.SupportedMetric.objects.get(key='key_name_3')

    lts_metric1_value = metric1.objects.collected_metrics.last().value
    lts_metric2_value = metric2.objects.collected_metrics.last().value
    lts_metric3_value = metric3.objects.collected_metrics.last().value

    already_calculated = models.CalculatedMeasure.objects.filter(
        measure=measure,
        data = {
            "lts_metric1": lts_metric1_value,
            "lts_metric2": lts_metric2_value,
            "lts_metric3": lts_metric3_value,
        }
    )

    if already_calculated:
        # TODO: Implementar a classe CalculatedMeasureSerializer
        data = serializers.CalculatedMeasureSerializer(already_calculated).data
        return Response(data)

    measure_value = clients.CoreClient.calculate_measure(
        measure.key,
        lts_metric1_value,
        lts_metric2_value,
        lts_metric3_value,
    )

    new_calculated_measure = models.CalculatedMeasure.objects.create(
        measure=measure,
        value=measure_value
        data = {
            "lts_metric1": lts_metric1_value,
            "lts_metric2": lts_metric2_value,
            "lts_metric3": lts_metric3_value,
        },
    )

    data = serializers.CalculatedMeasureSerializer(new_calculated_measure).data
    return Response(data)
