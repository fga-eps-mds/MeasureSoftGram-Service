from characteristics.models import (CalculatedCharacteristic,
                                    SupportedCharacteristic)
from characteristics.serializers import (
    CalculatedCharacteristicHistorySerializer,
    CharacteristicsCalculationsRequestSerializer,
    LatestCalculatedCharacteristicSerializer,
    SupportedCharacteristicSerializer)
from organizations.models import Product, Repository
from pre_configs.models import PreConfig
from resources import calculate_characteristics
from rest_framework import mixins, status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from utils.clients import CoreClient
from utils.exceptions import SubCharacteristicNotDefinedInPreConfiguration


class CalculateCharacteristicViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CharacteristicsCalculationsRequestSerializer
    queryset = SupportedCharacteristic.objects.all()

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
        # 1. Get validated data
        serializer = CharacteristicsCalculationsRequestSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        created_at = data['created_at']

        # 2. Get queryset
        characteristics_keys = [
            characteristic['key']
            for characteristic in data['characteristics']
        ]
        qs = SupportedCharacteristic.objects.filter(
            key__in=characteristics_keys
        ).prefetch_related(
            'subcharacteristics',
            'subcharacteristics__calculated_subcharacteristics',
        )

        # 3. Create Core request
        product = self.get_product()
        pre_config = product.pre_configs.first()

        core_params = {'characteristics': []}

        char: SupportedCharacteristic
        for char in qs:
            try:
                subchars_params = char.get_latest_subcharacteristics_params(
                    pre_config,
                )

            except SubCharacteristicNotDefinedInPreConfiguration as exc:
                return Response(
                    {'error': str(exc)},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            core_params['characteristics'].append({
                'key': char.key,
                'subcharacteristics': subchars_params,
            })

        calculate_response = calculate_characteristics(core_params)

        if calculate_response.get('code'):
            status_code = calculate_response.pop('code')
            return calculate_response(calculate_response, status=status_code)

        data = calculate_response

        calculated_values = {
            characteristic['key']: characteristic['value']
            for characteristic in data['characteristics']
        }

        # 5. Salvando o resultado

        calculated_characteristics = []
        repository = self.get_repository()

        for characteristic in qs:
            value = calculated_values[characteristic.key]

            calculated_characteristics.append(
                CalculatedCharacteristic(
                    characteristic=characteristic,
                    value=value,
                    repository=repository,
                    created_at=created_at,
                )
            )

        CalculatedCharacteristic.objects.bulk_create(calculated_characteristics)

        # 6. Retornando o resultado
        serializer = LatestCalculatedCharacteristicSerializer(
            qs,
            many=True,
            context=self.get_serializer_context(),
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupportedCharacteristicModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna todas as características suportadas pelo sistema
    """
    queryset = SupportedCharacteristic.objects.all()
    serializer_class = SupportedCharacteristicSerializer


class RepositoryCharacteristicMixin:

    def get_repository(self):
        return get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )

    def get_queryset(self):
        repository = self.get_repository()
        qs = repository.calculated_characteristics.all()
        qs = qs.values_list('characteristic', flat=True).distinct()
        return SupportedCharacteristic.objects.filter(id__in=qs)


class LatestCalculatedCharacteristicModelViewSet(
    RepositoryCharacteristicMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o último valor calculado da característica
    """
    queryset = SupportedCharacteristic.objects.prefetch_related(
        'calculated_characteristics'
    )
    serializer_class = LatestCalculatedCharacteristicSerializer

    def get_queryset(self):
        repository = get_object_or_404(
            Repository,
            id=self.kwargs['repository_pk'],
            product_id=self.kwargs['product_pk'],
            product__organization_id=self.kwargs['organization_pk'],
        )
        qs = repository.calculated_characteristics.all()
        qs = qs.values_list('characteristic', flat=True).distinct()
        return SupportedCharacteristic.objects.filter(id__in=qs)


class CalculatedCharacteristicHistoryModelViewSet(
    RepositoryCharacteristicMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o histórico de características calculadas
    """
    queryset = SupportedCharacteristic.objects.prefetch_related(
        'calculated_characteristics'
    )
    serializer_class = CalculatedCharacteristicHistorySerializer
