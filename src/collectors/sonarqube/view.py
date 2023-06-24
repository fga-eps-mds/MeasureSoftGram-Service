from rest_framework import mixins, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from collectors.sonarqube.serializers import SonarQubeJSONSerializer
from collectors.sonarqube.utils import import_sonar_metrics
from metrics.models import SupportedMetric
from organizations.models import Repository


class ImportSonarQubeMetricsViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    TODO: Isso não devia ser síncrono.
    A importação de métricas do sonarqube deveria ser uma tarefa assíncrona.
    """

    serializer_class = SonarQubeJSONSerializer
    queryset = SupportedMetric.objects.all()

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs["repository_pk"],
            product_id=self.kwargs["product_pk"],
            product__organization_id=self.kwargs["organization_pk"],
        )

    def create(self, request, *args, **kwargs):
        data = dict(request.data)
        repository = self.get_repository()
        json_data = import_sonar_metrics(data, repository)
        return Response(json_data)
