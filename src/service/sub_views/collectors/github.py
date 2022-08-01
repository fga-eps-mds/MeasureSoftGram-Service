"""
Views que realiza a coleta de métricas no repositório github
"""
from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

import utils
from service import models, serializers
from service.collectors import GithubMetricCollector
from service.serializers import GithubCollectorParamsSerializer
from utils.exceptions import GithubCollectorParamsException


<<<<<<< HEAD
def get_dynamic_key(key: str, threshold: int) -> str:
    dynamic_key = key.split('_in_the_last')[0]
    dynamic_key += f'_in_the_last_{threshold}_days'

    return dynamic_key
=======
def get_or_create_supported_metric(
    metric: dict,
) -> models.SupportedMetric:
    sup_metric, _ = models.SupportedMetric.objects.get_or_create(
        name=metric['name'],
        key=metric['key'],
        metric_type=metric['metric_type'],
    )
    return sup_metric
>>>>>>> b66f232... #134 - Add ci feedback time measure


def get_threshold(data):
    if 'issues_metrics_x_days' in data:
        threshold = data['issues_metrics_x_days']
    elif 'pipeline_metrics_x_days' in data:
        threshold = data['pipeline_metrics_x_days']
    else:
        raise GithubCollectorParamsException((
            'Currently the thresholds considered are: '
            '[issues_metrics_x_days, pipeline_metrics_x_days].'
        ))
    return threshold


def get_collector_instance(params_map, data):
    if not isinstance(data, dict):
        raise TypeError('data must be a dictionary')

    if not isinstance(params_map, dict):
        raise TypeError('params_map must be a dictionary')

    # Nomes das chaves serializadora
    url_key = params_map['__init__']['url']
    token_key = params_map['__init__']['token']

    url = data[url_key]
    token = data[token_key]

    return GithubMetricCollector(url, token)


def get_collector_metric_method_params(params_map, data):
    params: dict = params_map['metric_method']['method_params']

    return {
        param_name: data[serializer_key]
        for param_name, serializer_key in params.items()
    }


def calculate_metric_value(metric, data):
    params_map = metric['methods_params_map']
    collector = get_collector_instance(params_map, data)
    method = getattr(collector, params_map['metric_method']['method_name'])
    method_params = get_collector_metric_method_params(params_map, data)
    return method(**method_params)


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def import_github_metrics(request):
    serializer = GithubCollectorParamsSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    new_collected_metrics = []

    # TODO: Parallelize this for loop
    for metric in settings.GITHUB_METRICS:
        has_all_params = all(
            param in data for param in metric['api_params']
        )

        if not has_all_params:
            continue

        sup_metric = models.SupportedMetric.objects.get(
            key=metric['key']
        )

        threshold = get_threshold(data)

        dynamic_key = get_dynamic_key(metric['key'], threshold)

        # Calcula o valor da métrica desejada
        value = calculate_metric_value(metric, data)

        sup_metric.collected_metrics.create(value=value, dynamic_key=dynamic_key)
        new_collected_metrics.append(sup_metric)

    serializer = serializers.LatestCollectedMetricSerializer(
        new_collected_metrics,
        many=True,
    )

    return Response({'calculated_metrics': serializer.data})
