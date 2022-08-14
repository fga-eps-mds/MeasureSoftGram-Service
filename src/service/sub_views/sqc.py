from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

import utils
from service import clients, models, serializers


class SQCModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para cadastrar as medidas coletadas
    """
    queryset = models.SQC.objects.all()
    serializer_class = serializers.SQCSerializer


@api_view(['POST', 'HEAD', 'OPTIONS'])
def calculate_sqc(request):
    pre_config = models.PreConfig.objects.first()
    qs = models.SupportedMeasure.objects.all().prefetch_related(
        'metrics',
        'metrics__collected_metrics',
    )

    metrics_data = []

    for measure in qs:
        metric: models.SupportedMetric
        for metric in measure.metrics.all():
            metrics_data.append({
                'key': metric.key,
                'value': metric.get_latest_metric_value(),
                'measure_key': measure.key,
            })

    core_params = {
        'pre_config': pre_config.data,
        'metrics': metrics_data,
    }

    response = clients.CoreClient.calculate_sqc(core_params)

    if response.ok is False:
        return Response(response.text, status=response.status_code)

    data = response.json()

    sqc = models.SQC.objects.create(
        value=data['value'],
    )

    serializer = serializers.SQCSerializer(sqc)

    return Response(serializer.data, status=status.HTTP_201_CREATED)
