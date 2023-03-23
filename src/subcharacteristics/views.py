import utils
from organizations.models import Product, Repository
from resources import calculate_subcharacteristics
from rest_framework import mixins, status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from subcharacteristics.models import (CalculatedSubCharacteristic,
                                       SupportedSubCharacteristic)
from subcharacteristics.serializers import (
    CalculatedSubCharacteristicHistorySerializer,
    LatestCalculatedSubCharacteristicSerializer,
    SubCharacteristicsCalculationsRequestSerializer,
    SupportedSubCharacteristicSerializer)
from utils.clients import CoreClient


class CalculateSubCharacteristicViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SubCharacteristicsCalculationsRequestSerializer

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )

    def get_product(self):
        return get_object_or_404(
            Product,
            id=self.kwargs['product_pk'],
            organization_id=self.kwargs['organization_pk'],
        )

    def create(self, request, *args, **kwargs):
        serializer = SubCharacteristicsCalculationsRequestSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        created_at = data['created_at']

        # 2. get queryset
        subcharacteristics_keys = [
            subcharacteristic['key']
            for subcharacteristic in data['subcharacteristics']
        ]
        qs = SupportedSubCharacteristic.objects.filter(
            key__in=subcharacteristics_keys
        ).prefetch_related(
            'measures',
            'measures__calculated_measures',
        )

        product = self.get_product()
        pre_config = product.pre_configs.first()

        # 3. get core json response
        core_params = {'subcharacteristics': []}
        subchar: SupportedSubCharacteristic

        for subchar in qs:
            try:
                measure_params = subchar.get_latest_measure_params(pre_config)

            except utils.exceptions.MeasureNotDefinedInPreConfiguration as exc:
                return Response(
                    {'error': str(exc)},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            core_params['subcharacteristics'].append({
                'key': subchar.key,
                'measures': measure_params,
            })

        calculate_response = calculate_subcharacteristics(core_params)

        if calculate_response.get('code'):
            status_code = calculate_response.pop('code')
            return calculate_response(calculate_response, status=status_code)

        data = calculate_response

        # 4. Save data
        calculated_values = {
            subcharacteristic['key']: subcharacteristic['value']
            for subcharacteristic in data['subcharacteristics']
        }

        calculated_subcharacteristics = []

        repository = self.get_repository()

        subchar: SupportedSubCharacteristic
        for subchar in qs:
            value = calculated_values[subchar.key]

            calculated_subcharacteristics.append(
                CalculatedSubCharacteristic(
                    subcharacteristic=subchar,
                    value=value,
                    repository=repository,
                    created_at=created_at,
                )
            )

        CalculatedSubCharacteristic.objects.bulk_create(
            calculated_subcharacteristics
        )

        # 5. Return data
        serializer = LatestCalculatedSubCharacteristicSerializer(
            qs,
            many=True,
            context=self.get_serializer_context(),
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupportedSubCharacteristicModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna todas as subcaracterísticas suportadas pelo sistema
    """
    queryset = SupportedSubCharacteristic.objects.all()
    serializer_class = SupportedSubCharacteristicSerializer


class RepositorySubCharacteristicMixin:
    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )

    def get_queryset(self):
        repository = self.get_repository()
        qs = repository.calculated_subcharacteristics.all()
        qs = qs.values_list('subcharacteristic', flat=True).distinct()
        return SupportedSubCharacteristic.objects.filter(id__in=qs)


class LatestCalculatedSubCharacteristicModelViewSet(
    RepositorySubCharacteristicMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o último valor calculado da subcaracterística
    """
    queryset = SupportedSubCharacteristic.objects.prefetch_related(
        'calculated_subcharacteristics',
    )
    serializer_class = LatestCalculatedSubCharacteristicSerializer


class CalculatedSubCharacteristicHistoryModelViewSet(
    RepositorySubCharacteristicMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o histórico de subcaracterísticas calculadas
    """
    queryset = SupportedSubCharacteristic.objects.prefetch_related(
        'calculated_subcharacteristics',
    )
    serializer_class = CalculatedSubCharacteristicHistorySerializer
