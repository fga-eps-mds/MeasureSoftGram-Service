from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from measures.models import SupportedMeasure
from metrics.models import SupportedMetric
from pre_configs.models import PreConfig
from sqc.models import SQC
from sqc.serializers import SQCSerializer
from utils.clients import CoreClient


class LatestCalculatedSQCViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = SQC.objects.all()
    serializer_class = SQCSerializer

    def list(self, request, *args, **kwargs):
        latest_sqc = SQC.objects.first()
        serializer = self.get_serializer(latest_sqc, many=True)
        return Response(serializer.data)


class CalculatedSQCHistoryModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para cadastrar as medidas coletadas
    """
    queryset = SQC.objects.all()
    serializer_class = SQCSerializer


class CalculateSQC(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SQCSerializer

    def create(self, request, *args, **kwargs):
        pre_config = PreConfig.objects.first()

        qs = SupportedMeasure.objects.all().prefetch_related(
            'metrics',
            'metrics__collected_metrics',
        )

        metrics_data = []

        for measure in qs:
            metric: SupportedMetric
            for metric in measure.metrics.all():
                metrics_data.append({
                    'key': metric.key,
                    'value': metric.get_latest_metric_value(),
                    'measure_key': measure.key,
                })

        core_params = {
            'pre_config': pre_config.data,
            'metrics': metrics_data,
        }

        response = CoreClient.calculate_sqc(core_params)

        if response.ok is False:
            return Response(response.text, status=response.status_code)

        data = response.json()

        sqc = SQC.objects.create(
            value=data['value'],
        )

        serializer = SQCSerializer(sqc)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
