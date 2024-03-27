"""
Views que realiza a coleta de métricas no repositório github
"""
import concurrent.futures

from django.conf import settings
from rest_framework import mixins, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from collectors.github import utils
from collectors.github.serializers import GithubCollectorParamsSerializer
from metrics.models import SupportedMetric
from metrics.serializers import LatestCollectedMetricSerializer
from organizations.models import Repository


def collect_metric_from_github(
    metric, data, new_collected_metrics, repository
):
    has_all_params = all(param in data for param in metric['api_params'])

    if not has_all_params:
        return

    sup_metric = SupportedMetric.objects.get(key=metric['key'])

    threshold = utils.get_threshold(data)

    dynamic_key = utils.get_dynamic_key(metric['key'], threshold)

    # Calcula o valor da métrica desejada
    value = utils.calculate_metric_value(metric, data)

    repository.collected_metrics.create(
        value=value,
        dynamic_key=dynamic_key,
        metric=sup_metric,
    )

    new_collected_metrics.append(sup_metric)


class ImportGithubMetricsViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    TODO: Isso não devia ser síncrono.
    A importação de métricas do github deveria ser uma tarefa assíncrona.
    """

    serializer_class = GithubCollectorParamsSerializer
    queryset = SupportedMetric.objects.all()

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )

    def create(self, request, *args, **kwargs):
        serializer = GithubCollectorParamsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        new_collected_metrics = []
        repository = self.get_repository()

        with concurrent.futures.ThreadPoolExecutor() as e:
            futures = []

            for metric in settings.GITHUB_METRICS:
                futures.append(
                    e.submit(
                        collect_metric_from_github,
                        metric,
                        data,
                        new_collected_metrics,
                        repository,
                    )
                )

            for r in concurrent.futures.as_completed(futures):
                r.result()

        serializer = LatestCollectedMetricSerializer(
            new_collected_metrics,
            many=True,
        )

        return Response({'collected metrics': serializer.data})
