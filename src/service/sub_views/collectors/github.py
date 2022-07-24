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


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def import_github_metrics(request):
    serializer = GithubCollectorParamsSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    new_metrics = []

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

        params_map = metric['methods_params_map']

        # Nomes das chaves serializadora
        url_key = params_map['__init__']['url']
        token_key = params_map['__init__']['token']

        url = data[url_key]
        token = data[token_key]

        collector = GithubMetricCollector(url, token)

        method = getattr(collector, params_map['metric_method']['method_name'])
        params: dict = params_map['metric_method']['method_params']

        method_params = {
            param_name: data[serializer_key]
            for param_name, serializer_key in params.items()
        }

        value = method(**method_params)

        colleted_metric = sup_metric.collected_metrics.create(value=value)
        new_metrics.append(colleted_metric)

    serializer = serializers.CollectedMetricSerializer(
        new_metrics,
        many=True,
    )

    return Response({'calculated_metrics': serializer.data})
