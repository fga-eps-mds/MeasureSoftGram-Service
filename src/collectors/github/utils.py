from collectors.github import GithubMetricCollector
from utils.exceptions import GithubCollectorParamsException


def get_dynamic_key(key: str, threshold: int) -> str:
    """
    Retorna a key genérica com o threshold, retornando assim a key dinâmica
    """
    dynamic_key = key.split('_in_the_last')[0]
    dynamic_key += f'_in_the_last_{threshold}_days'
    return dynamic_key


def get_threshold(data):
    if 'issues_metrics_x_days' in data:
        threshold = data['issues_metrics_x_days']
    elif 'pipeline_metrics_x_days' in data:
        threshold = data['pipeline_metrics_x_days']
    else:
        raise GithubCollectorParamsException(
            (
                'Currently the thresholds considered are: '
                '[issues_metrics_x_days, pipeline_metrics_x_days].'
            )
        )
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
