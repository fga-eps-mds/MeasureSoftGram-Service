from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from service.models import CollectedMetric, SupportedMetric
from service.serializers import CollectedMetricSerializer
from utils import namefy


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def import_sonar_metrics(request):
    """
    Endpoint que recebe um o JSON obtido na API do SonarQube,
    extrai os valores das métricas contidas e salva no banco de dados.
    """
    data = dict(request.data)
    collected_metrics = []
    supported_metrics = {}

    for supported_metric in SupportedMetric.objects.all():
        supported_metrics[supported_metric.key] = supported_metric

    for component in data['components']:
        for metric in component['measures']:
            obj = {}
            obj['qualifier'] = component['qualifier']
            obj['path'] = component['path']

            if metric['metric'] not in supported_metrics:
                supported_metrics[metric['metric']] = SupportedMetric.objects.create(
                    key=metric['metric'],
                    metric_type=SupportedMetric.SupportedMetricTypes.FLOAT,
                    name=namefy(metric['metric'])
                )

            obj['metric'] = supported_metrics[metric['metric']]
            obj['value'] = float(metric['value'])

            collected_metrics.append(CollectedMetric(**obj))

    saved_metrics = CollectedMetric.objects.bulk_create(collected_metrics)

    return Response(CollectedMetricSerializer(saved_metrics, many=True).data)
