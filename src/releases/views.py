from core.transformations import diff
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from characteristics.models import CalculatedCharacteristic
from entity_trees.services import resolve_release_configuration
from organizations.mixins import UserScopedMixin
from organizations.models import Repository
from releases.entity_analysis import (
    LEVELS,
    MetricWithoutRepositoryValue,
    get_entity_analysis,
    get_entity_catalog,
)
from releases.models import Release
from releases.serializers import CheckReleaseSerializer, ReleaseAllSerializer, ReleaseSerializer
from releases.service import (
    calculate_diff,
    get_accomplished_values,
    get_arrays_diff,
    get_calculated_characteristic_by_ids_repositories,
    get_norm_diff,
    get_planned_values,
    get_process_calculated_characteristics,
    update_release_end_at,
)


class ReleaseModelViewSet(UserScopedMixin, viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer

    def get_queryset(self):
        product = self.get_product()

        return (
            Release.objects.filter(product=product)
            .select_related('goal', 'created_by')
            .prefetch_related('repositories')
        )

    @action(detail=False, methods=["get"], url_path="is-valid")
    def check_release(self, request, *args, **kwargs):
        product = self.get_product()

        name_release = request.query_params.get("nome")
        init_date = request.query_params.get("dt-inicial")
        final_date = request.query_params.get("dt-final")

        serializer = CheckReleaseSerializer(
            data={
                "nome": name_release,
                "dt_inicial": init_date,
                "dt_final": final_date,
            }  # type: ignore
        )
        serializer.is_valid(raise_exception=True)

        release = Release.objects.filter(
            product=product,
            release_name=name_release,
        ).first()

        if release:
            return Response(
                data={"detail": "Já existe uma release com este nome"},
                status=400,
            )

        release = Release.objects.filter(
            product=product,
            start_at__lte=final_date,
            end_at__gte=init_date,
        )

        if release.count() > 1:
            return Response(
                data={"detail": "Já existem múltiplas releases neste período"},
                status=400,
            )
        elif release:
            release_data = ReleaseSerializer(release.first()).data
            return Response(
                data={
                    "detail": "Já existe uma release neste período",
                    "release": release_data,
                },
                status=400,
            )

        return Response({"message": "Parametros válidos para criação de Release"})

    @action(
        detail=False,
        methods=["get"],
        url_path=r"(?P<id>\d+)/planeed-x-accomplished",
    )
    def planned_x_accomplished(self, request, id=None, *args, **kwargs):
        if id:
            id = int(id)
        else:
            return Response({"detail": "Id da release não informado"}, status=400)

        accomplished = {}
        release = Release.objects.filter(id=id).first()
        result_calculated = CalculatedCharacteristic.objects.filter(release=release).all()

        if len(result_calculated) > 0:
            accomplished = get_process_calculated_characteristics(list(result_calculated))
        else:
            if release.repositories.exists():
                ids_repositories = list(release.repositories.values_list("id", flat=True))
            else:
                product_key = int(self.kwargs["product_pk"])
                ids_repositories = list(
                    Repository.objects.filter(product_id=product_key).values_list("id", flat=True).all()
                )

            result_calculated = get_calculated_characteristic_by_ids_repositories(ids_repositories)
            accomplished = get_process_calculated_characteristics(list(result_calculated))
        if len(accomplished.keys()) > 0:
            for key_repository in accomplished:
                arrays_rp_rd = get_arrays_diff(release.goal.data, accomplished[key_repository])
                result = diff(arrays_rp_rd[0], arrays_rp_rd[1])
                accomplished[key_repository] = result
        else:
            accomplished = None

        if release:
            serializer = ReleaseAllSerializer(release)
            return Response(
                {
                    "release": serializer.data,
                    "planned": {
                        "reliability": release.goal.data["reliability"] / 100,
                        "maintainability": release.goal.data["maintainability"] / 100,
                    },
                    "accomplished": accomplished,
                }
            )
        else:
            return Response({"detail": "Release não encontrada"}, status=404)

    @action(detail=True, methods=["get"])
    def analysis_data(self, request, pk=None, *args, **kwargs):
        release_id = pk
        product_pk = self.kwargs["product_pk"]

        release = Release.objects.filter(id=release_id).first()

        if release is None:
            return Response({"detail": "Release não encontrada"}, status=404)

        repositories_ids = list(Repository.objects.filter(product_id=product_pk).values_list("id", flat=True).all())

        serialized_release = ReleaseAllSerializer(release).data
        planned_values = get_planned_values(release)
        accomplished_values = get_accomplished_values(release, repositories_ids)
        accomplished_with_norm_diff = get_norm_diff(planned_values, accomplished_values)
        accomplished_values_with_diff_and_norm_diff = calculate_diff(planned_values, accomplished_with_norm_diff)

        return Response(
            {
                "release": serialized_release,
                "planned": planned_values,
                "accomplished": accomplished_values_with_diff_and_norm_diff,
            }
        )

    @action(detail=True, methods=["put"], url_path="update-end-at")
    def update_end_at(self, request, pk=None, *args, **kwargs):
        # Obtendo o novo valor de end_at da requisição
        new_end_at = request.data.get("end_at")

        if not new_end_at:
            return Response({"detail": "O campo end_at é obrigatório."}, status=400)

        # Utilizando o serviço para atualizar o end_at
        release = update_release_end_at(pk, new_end_at)  # type: ignore

        if release:
            serializer = self.get_serializer(release)
            return Response(serializer.data, status=200)
        else:
            return Response({"detail": "Release não encontrada"}, status=404)


class EntityAnalysisViewSet(UserScopedMixin, viewsets.ViewSet):
    """
    Análise por entidade (US21.02): valor de uma entidade do modelo em cada
    repositório do produto, numa release, com os filhos da entidade.
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_release(self):
        release_id = self.request.query_params.get("release_id")
        if not release_id or not release_id.isdigit():
            return None
        return get_object_or_404(
            Release.objects.select_related("goal", "product"),
            id=int(release_id),
            product=self.get_product(),
        )

    def list(self, request, *args, **kwargs):
        level = request.query_params.get("level")
        key = request.query_params.get("key")

        if level not in LEVELS:
            return Response({"detail": f"O parâmetro level deve ser um de: {', '.join(LEVELS)}."}, status=400)
        if not key:
            return Response({"detail": "O parâmetro key é obrigatório."}, status=400)

        release = self.get_release()
        if release is None:
            return Response({"detail": "O parâmetro release_id é obrigatório."}, status=400)

        configuration = resolve_release_configuration(release.product, release)
        try:
            analysis = get_entity_analysis(release, configuration, level, key) if configuration else None
        except MetricWithoutRepositoryValue:
            return Response({"detail": "Esta métrica não tem valor por repositório."}, status=400)
        if analysis is None:
            return Response({"detail": "Entidade não faz parte da configuração da release."}, status=404)

        return Response(analysis)

    @action(detail=False, methods=["get"])
    def entities(self, request, *args, **kwargs):
        release = self.get_release()
        if release is None:
            return Response({"detail": "O parâmetro release_id é obrigatório."}, status=400)

        configuration = resolve_release_configuration(release.product, release)
        if configuration is None:
            return Response({level: [] for level in LEVELS})

        return Response(get_entity_catalog(release, configuration))
