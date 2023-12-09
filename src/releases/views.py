from releases.serializers import CheckReleaseSerializer, ReleaseSerializer, ReleaseAllSerializer
from releases.models import Release
from goals.models import Goal

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


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
            }
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
        url_path='(?P<id>\d+)/planeed-x-accomplished'
    )
    def planned_x_accomplished(self, request, id=None,*args, **kwargs):
        if id:
            id = int(id)
        else:
            return Response(
                {'detail': 'Id da release não informado'}, status=400
            )

        release = Release.objects.filter(id=id).first()

        if release:
            serializer = ReleaseAllSerializer(release)
            return Response({
                'release': serializer.data,
                'planned': release.goal.data,
                'accomplished': None,
            })
        else:
            return Response(
                {'detail': 'Release não encontrada'}, status=404
            )
