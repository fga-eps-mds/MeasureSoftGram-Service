from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from characteristics.serializers import (
    CalculatedCharacteristicHistorySerializer,
    CharacteristicsCalculationsRequestSerializer,
    LatestCalculatedCharacteristicSerializer,
    SupportedCharacteristicSerializer,
)
from pre_configs.models import PreConfig
from utils.clients import CoreClient
from utils.exceptions import SubCharacteristicNotDefinedInPreConfiguration


class CalculateCharacteristicViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CharacteristicsCalculationsRequestSerializer

    def create(self, request, *args, **kwargs):
        # 1. Get validated data
        serializer = CharacteristicsCalculationsRequestSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

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
        pre_config = PreConfig.objects.first()

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

        response = CoreClient.calculate_characteristic(core_params)

        if response.ok is False:
            return Response(response.text, status=response.status_code)

        data = response.json()

        calculated_values = {
            characteristic['key']: characteristic['value']
            for characteristic in data['characteristics']
        }

        # 5. Salvando o resultado

        calculated_characteristics = []

        for characteristic in qs:
            value = calculated_values[characteristic.key]

            calculated_characteristics.append(
                CalculatedCharacteristic(
                    characteristic=characteristic,
                    value=value,
                )
            )

        CalculatedCharacteristic.objects.bulk_create(
            calculated_characteristics,
        )

        # 6. Retornando o resultado
        serializer = LatestCalculatedCharacteristicSerializer(qs, many=True)

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


class LatestCalculatedCharacteristicModelViewSet(
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


class CalculatedCharacteristicHistoryModelViewSet(
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
