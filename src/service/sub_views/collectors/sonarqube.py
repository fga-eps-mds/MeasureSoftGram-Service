from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from service.models import CollectedMetric, SupportedMetric
from service.serializers import CollectedMetricSerializer
from utils import namefy


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def import_sonar_metrics_view(request):
    """
    Endpoint que recebe um o JSON obtido na API do SonarQube,
    extrai os valores das métricas contidas e salva no banco de dados.
    """
    data = dict(request.data)
    return import_sonar_metrics(data)


def import_sonar_metrics(data):

    supported_metrics = {
        supported_metric.key: supported_metric
        for supported_metric in SupportedMetric.objects.all()
    }

    # List used to bulk create metrics
    collected_metrics = []

    for component in data['components']:
        for obj in component['measures']:
            metric_key = obj['metric']
            metric_name = namefy(metric_key)
            metric_value = obj['value']

            if obj['metric'] not in supported_metrics:
                supported_metrics[metric_key] = SupportedMetric.objects.create(
                    key=metric_key,
                    metric_type=SupportedMetric.SupportedMetricTypes.FLOAT,
                    name=metric_name,
                )

            obj = {
                'qualifier': component['qualifier'],
                'path': component['path'],
                'metric': supported_metrics[metric_key],
                'value': float(metric_value),
            }

            in_memory_metric = CollectedMetric(**obj)
            collected_metrics.append(in_memory_metric)

    saved_metrics = CollectedMetric.objects.bulk_create(collected_metrics)

    json_data = CollectedMetricSerializer(saved_metrics, many=True).data
    return Response(json_data)
