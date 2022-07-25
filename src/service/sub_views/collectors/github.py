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


def get_or_create_supported_metric(
    metric: dict,
    threshold: int,
) -> models.SupportedMetric:
    m_name = metric['name']
    m_name = m_name.split(' in the last')[0]
    m_name += f' in the last {threshold} days'

    sup_metric, _ = models.SupportedMetric.objects.get_or_create(
        name=m_name,
        key=utils.keyfy(m_name),
        metric_type=metric['metric_type'],
    )
    return sup_metric


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

        threshold = get_threshold(data)

        # O nome da métrica está atrelado com o threshold, desse
        # modo é preciso verificar se a métrica que o usuário está
        # querendo calcular já existe, e caso não exista, criá-la
        sup_metric = get_or_create_supported_metric(
            metric,
            threshold,
        )

        # Calcula o valor da métrica desejada
        value = calculate_metric_value(metric, data)

        sup_metric.collected_metrics.create(value=value)
        new_collected_metrics.append(sup_metric)

    serializer = serializers.LatestCollectedMetricSerializer(
        new_collected_metrics,
        many=True,
    )

    return Response({'calculated_metrics': serializer.data})
