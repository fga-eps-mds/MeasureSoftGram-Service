from rest_framework import mixins, viewsets
from rest_framework.response import Response

from collectors.sonarqube.serializers import SonarQubeJSONSerializer
from collectors.sonarqube.utils import import_sonar_metrics


class ImportSonarQubeMetricsViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    TODO: Isso não devia ser síncrono.
    A importação de métricas do sonarqube deveria ser uma tarefa assíncrona.
    """
    serializer_class = SonarQubeJSONSerializer

    def create(self, request, *args, **kwargs):
        data = dict(request.data)
        json_data = import_sonar_metrics(data)
        return Response(json_data)
