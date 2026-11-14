from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from organizations.mixins import UserScopedMixin
from organizations.models import Repository
from organizations.quality_bands import build_bands, get_limits
from tsqmi.serializers import TSQMISerializer
from utils.badge import BADGE_SWAGGER_RESPONSE, is_stale, render_badge_svg, render_stale_badge_svg
from utils.schema import record_schema


class LatestCalculatedTSQMIViewSet(
    UserScopedMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TSQMISerializer

    def get_queryset(self):
        repository = self.get_repository()
        return repository.calculated_tsqmis.all()

    # sem TSQMI calculado, o serializer devolve {"created_at": null}
    @swagger_auto_schema(responses={200: record_schema("LatestRepositoryTSQMI", latest=True)})
    def list(self, request, *args, **kwargs):
        repository = self.get_repository()
        latest_tsqmi = repository.calculated_tsqmis.first()
        serializer = self.get_serializer(latest_tsqmi)
        return Response(serializer.data)


class LatestCalculatedTSQMIBadgeViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TSQMISerializer
    permission_classes = (AllowAny,)
    authentication_classes = []

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs["repository_pk"],
            product_id=self.kwargs["product_pk"],
            product__organization_id=self.kwargs["organization_pk"],
        )

    @swagger_auto_schema(responses={200: BADGE_SWAGGER_RESPONSE})
    def list(self, request, *args, **kwargs):
        repository = self.get_repository()
        latest_tsqmi = repository.calculated_tsqmis.first()

        if latest_tsqmi is None or is_stale(latest_tsqmi.created_at):
            return render_stale_badge_svg("MeasureSoftGram")

        return render_badge_svg("MeasureSoftGram", latest_tsqmi.value, build_bands(get_limits(repository.product)))


class CalculatedTSQMIHistoryModelViewSet(
    UserScopedMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para cadastrar as medidas coletadas
    """

    serializer_class = TSQMISerializer

    def get_queryset(self):
        repository = self.get_repository()
        return repository.calculated_tsqmis.all().reverse()
