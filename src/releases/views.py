from releases.serializers import (
    CheckReleaseSerializer,
    ReleaseSerializer,
    ReleaseAllSerializer,
)
from releases.models import Release
from goals.models import Goal
from organizations.models import Repository
from characteristics.models import CalculatedCharacteristic

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.transformations import diff, norm_diff


class CreateReleaseModelViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer

    def get_queryset(self):
        product_key = self.kwargs['product_pk']

        return Release.objects.filter(product=product_key)

    @action(detail=False, methods=['get'], url_path='is-valid')
    def check_release(self, request, *args, **kwargs):
        product_key = self.kwargs['product_pk']

        name_release = request.query_params.get('nome')
        init_date = request.query_params.get('dt-inicial')
        final_date = request.query_params.get('dt-final')

        serializer = CheckReleaseSerializer(
            data={
                'nome': name_release,
                'dt_inicial': init_date,
                'dt_final': final_date,
            }  # type: ignore
        )
        serializer.is_valid(raise_exception=True)

        release = Release.objects.filter(
            product=product_key,
            release_name=name_release,
        ).first()

        if release:
            return Response(
                data={'detail': 'Já existe uma release com este nome'},
                status=400,
            )

        release = Release.objects.filter(
            product=product_key,
            start_at__gte=init_date,
            start_at__lte=final_date,
            end_at__gte=init_date,
            end_at__lte=final_date,
        ).first()

        if release:
            return Response(
                data={'detail': 'Já existe uma release neste período'},
                status=400,
            )

        return Response(
            {'message': 'Parametros válidos para criação de Release'}
        )

    @action(
        detail=False,
        methods=['get'],
        url_path=r'(?P<id>\d+)/planeed-x-accomplished',
    )
    def planned_x_accomplished(self, request, id=None, *args, **kwargs):
        if id:
            id = int(id)
        else:
            return Response(
                {'detail': 'Id da release não informado'}, status=400
            )

        accomplished = {}

        release = Release.objects.filter(id=id).first()

        result_calculated = CalculatedCharacteristic.objects.filter(
            release=release
        ).all()

        if len(result_calculated) > 0:
            for calculated_characteristic in result_calculated:
                caracteristica = calculated_characteristic.characteristic.key
                repository = calculated_characteristic.repository.name

                if repository not in accomplished.keys():
                    accomplished[repository] = {}
                accomplished[repository].update(
                    {caracteristica: calculated_characteristic.value}
                )
        else: 
            result_calculated = []
            product_key = int(self.kwargs['product_pk'])
            ids_repositories = list(
                Repository.objects
                .filter(product_id=product_key)
                .values_list('id', flat=True).all()
            )

            for id_repository in ids_repositories:
                calculated_characteristic = (
                    CalculatedCharacteristic.objects
                    .filter(
                        repository_id=id_repository,
                        release=None
                    ).all().order_by('-created_at')[:2])
                result_calculated = result_calculated + list(calculated_characteristic)

            for calculated_characteristic in result_calculated:
                caracteristica = calculated_characteristic.characteristic.key
                repository = calculated_characteristic.repository.name

                if repository not in accomplished.keys():
                    accomplished[repository] = {}
                accomplished[repository].update(
                    {caracteristica: calculated_characteristic.value}
                )

        if len(accomplished.keys()) > 0:
            for key_repository in accomplished:
                result = diff(
                    [
                        release.goal.data['reliability'] / 100,  # type: ignore
                        release.goal.data['maintainability'] / 100,  # type: ignore
                    ],
                    [
                        accomplished[key_repository]['reliability'],
                        accomplished[key_repository]['maintainability'],
                    ],
                )
                accomplished[key_repository] = result
        else:
            accomplished = None

        if release:
            serializer = ReleaseAllSerializer(release)
            return Response(
                {
                    'release': serializer.data,
                    'planned': {
                        'reliability': release.goal.data['reliability'] / 100,
                        'maintainability': release.goal.data['maintainability']
                        / 100,
                    },
                    'accomplished': accomplished,
                }
            )
        else:
            return Response({'detail': 'Release não encontrada'}, status=404)
