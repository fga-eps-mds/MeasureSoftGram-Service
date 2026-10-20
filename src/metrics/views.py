from rest_framework import mixins, permissions, serializers, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from metrics.distribution import get_metric_reference, get_repository_distribution
from metrics.models import SupportedMetric
from metrics.serializers import (
    CollectedMetricHistorySerializer,
    LatestCollectedMetricSerializer,
    MetricDistributionQuerySerializer,
    SupportedMetricSerializer,
)
from organizations.mixins import UserScopedMixin
from releases.entity_analysis import get_release_repositories
from releases.models import Release


class SupportedMetricModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna todas as métricas suportadas pelo sistema
    """

    queryset = SupportedMetric.objects.all()
    serializer_class = SupportedMetricSerializer


class RepositoryMetricsMixin(UserScopedMixin):
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        repository = self.get_repository()
        serializer.save(repository=repository)

    def get_queryset(self):
        repository = self.get_repository()
        qs = repository.collected_metrics.all()
        qs = qs.values_list("metric", flat=True).distinct()
        return SupportedMetric.objects.filter(id__in=qs)


class LatestCollectedMetricModelViewSet(
    RepositoryMetricsMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para ler o valor mais recente das métricas coletadas
    """

    queryset = SupportedMetric.objects.prefetch_related("collected_metrics")

    serializer_class = LatestCollectedMetricSerializer


class CollectedMetricHistoryModelViewSet(
    RepositoryMetricsMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para ler o histórico de métricas coletadas

    TODO: Criar uma classe de paginação (
        https://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style
    )
    """

    queryset = SupportedMetric.objects.prefetch_related(
        "collected_metrics",
    )
    serializer_class = CollectedMetricHistorySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["start_at"] = self.request.query_params.get("start_at")
        context["end_at"] = self.request.query_params.get("end_at")
        context["qualifier"] = self.request.query_params.get("qualifier")
        return context


def _local_datetime(value):
    return serializers.DateTimeField().to_representation(value) if value else None


class MetricDistributionViewSet(UserScopedMixin, viewsets.ViewSet):
    """
    Distribuição de uma métrica entre os arquivos dos repositórios do produto,
    na última coleta dentro da janela da release (US21.03).
    """

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        product = self.get_product()
        params = MetricDistributionQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        metric_key = params.validated_data["metric"]
        repository_id = params.validated_data.get("repository_id")
        release = get_object_or_404(Release, id=params.validated_data["release_id"], product=product)

        if repository_id is not None:
            repositories = [get_object_or_404(product.repositories.all(), id=repository_id)]
        else:
            # mesma seleção e ordem (nome) da Análise por Entidade
            repositories = get_release_repositories(release)

        distributions = []
        for repository in repositories:
            distribution = get_repository_distribution(repository, metric_key, release)
            distribution["collected_at"] = _local_datetime(distribution["collected_at"])
            if repository_id is None:
                # comparação entre repositórios: só o resumo (CA6)
                distribution.pop("files")
            distributions.append(
                {"repository_id": repository.id, "repository_name": repository.name, **distribution}
            )

        return Response(
            {
                "release": {
                    "id": release.id,
                    "release_name": release.release_name,
                    "start_at": _local_datetime(release.start_at),
                    "end_at": _local_datetime(release.end_at),
                },
                "metric": metric_key,
                "reference": get_metric_reference(product, release, metric_key),
                "repositories": distributions,
            }
        )
