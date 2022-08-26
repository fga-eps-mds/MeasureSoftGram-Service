from metrics.models import CollectedMetric, SupportedMetric
from metrics.serializers import CollectedMetricSerializer
from utils import namefy


def import_sonar_metrics(data, only_create_supported_metrics=False):
    """
    Refatorar essa função para separar a criação das
    métricas da criação dos dados das métricas.

    TODO: Refatorar essa função
    """
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

    if only_create_supported_metrics:
        return {}

    saved_metrics = CollectedMetric.objects.bulk_create(collected_metrics)

    return CollectedMetricSerializer(saved_metrics, many=True).data
