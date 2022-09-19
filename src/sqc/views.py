from rest_framework import mixins, status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from measures.models import SupportedMeasure
from metrics.models import SupportedMetric
from organizations.models import Repository
from sqc.models import SQC
from sqc.serializers import SQCCalculationRequestSerializer, SQCSerializer
from utils.clients import CoreClient


class LatestCalculatedSQCViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SQCSerializer

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )

    def get_queryset(self):
        repository = self.get_repository()
        return repository.calculated_sqcs.all()

    def list(self, request, *args, **kwargs):
        repository = self.get_repository()
        latest_sqc = repository.calculated_sqcs.first()
        serializer = self.get_serializer(latest_sqc)
        return Response(serializer.data)


class CalculatedSQCHistoryModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para cadastrar as medidas coletadas
    """
    serializer_class = SQCSerializer

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )

    def get_queryset(self):
        repository = get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )
        return repository.calculated_sqcs.all().reverse()


class CalculateSQC(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SQCSerializer

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )

    def create(self, request, *args, **kwargs):
        serializer = SQCCalculationRequestSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        created_at = serializer.validated_data['created_at']

        repository: Repository = self.get_repository()
        pre_config = repository.product.pre_configs.first()

        qs = repository.calculated_measures.all()
        measures_ids = set(qs.values_list('measure', flat=True).distinct())

        qs = SupportedMeasure.objects.filter(id__in=measures_ids)
        qs = qs.prefetch_related(
            'metrics',
            'metrics__collected_metrics',
        )

        metrics_data = []
        smallest_list_size = None

        for measure in qs:
            metrics = measure.metrics.all()

            metric: SupportedMetric
            for metric in metrics:
                value = metric.get_latest_metric_value(repository)

                if isinstance(value, list):
                    smallest_list_size = min(
                        smallest_list_size or len(value),
                        len(value),
                    )

                if value is None:
                    value = 0

                metrics_data.append({
                    'key': metric.key,
                    'value': value,
                    'measure_key': measure.key,
                })

        # TODO: Isso é um workaround para o problema de
        # métricas de uma medida com trabalhos diferentes
        if smallest_list_size:
            for metric in metrics_data:
                if isinstance(metric['value'], list):
                    metric['value'] = metric['value'][:smallest_list_size]

        core_params = {
            'pre_config': pre_config.data,
            'metrics': metrics_data,
        }

        response = CoreClient.calculate_sqc(core_params)

        if response.ok is False:
            return Response(response.content, status=response.status_code)

        data = response.json()

        sqc = SQC.objects.create(
            repository=repository,
            value=data['value'],
            created_at=created_at,
        )

        serializer = SQCSerializer(sqc)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
