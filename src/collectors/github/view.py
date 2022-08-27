"""
Views que realiza a coleta de métricas no repositório github
"""
from django.conf import settings
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from collectors.github import utils
from collectors.github.serializers import GithubCollectorParamsSerializer
from metrics.models import SupportedMetric
from metrics.serializers import LatestCollectedMetricSerializer


class ImportGithubMetricsViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    TODO: Isso não devia ser síncrono.
    A importação de métricas do github deveria ser uma tarefa assíncrona.
    """
    serializer_class = GithubCollectorParamsSerializer

    def create(self, request, *args, **kwargs):
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

            sup_metric = SupportedMetric.objects.get(key=metric['key'])

            threshold = utils.get_threshold(data)

            dynamic_key = utils.get_dynamic_key(metric['key'], threshold)

            # Calcula o valor da métrica desejada
            value = utils.calculate_metric_value(metric, data)

            sup_metric.collected_metrics.create(value=value, dynamic_key=dynamic_key)
            new_collected_metrics.append(sup_metric)

        serializer = LatestCollectedMetricSerializer(
            new_collected_metrics,
            many=True,
        )

        return Response({'collected metrics': serializer.data})
