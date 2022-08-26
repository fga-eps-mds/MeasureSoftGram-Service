from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

import utils
from utils.clients import CoreClient

from subcharacteristics.models import (
    SupportedSubCharacteristic,
    CalculatedSubCharacteristic,
)

from pre_configs.models import (
    PreConfig,
)

from subcharacteristics.serializers import (
    SubCharacteristicsCalculationsRequestSerializer,
    LatestCalculatedSubCharacteristicSerializer,
    SupportedSubCharacteristicSerializer,
    CalculatedSubCharacteristicHistorySerializer,
)


class CalculateSubCharacteristicViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SubCharacteristicsCalculationsRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = SubCharacteristicsCalculationsRequestSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

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

        pre_config = PreConfig.objects.first()

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
        response = CoreClient.calculate_subcharacteristic(core_params)

        if response.ok is False:
            return Response(response.text, status=response.status_code)

        data = response.json()

        # 4. Save data
        calculated_values = {
            subcharacteristic['key']: subcharacteristic['value']
            for subcharacteristic in data['subcharacteristics']
        }

        calculated_subcharacteristics = []

        subchar: SupportedSubCharacteristic
        for subchar in qs:
            value = calculated_values[subchar.key]

            calculated_subcharacteristics.append(
                CalculatedSubCharacteristic(
                    subcharacteristic=subchar,
                    value=value,
                )
            )

        CalculatedSubCharacteristic.objects.bulk_create(
            calculated_subcharacteristics
        )

        # 5. Return data
        serializer = LatestCalculatedSubCharacteristicSerializer(qs, many=True)

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


class LatestCalculatedSubCharacteristicModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o último valor calculado da subcaracterística
    """
    queryset = SupportedSubCharacteristic.objects.prefetch_related('calculated_subcharacteristics')
    serializer_class = LatestCalculatedSubCharacteristicSerializer


class CalculatedSubCharacteristicHistoryModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o histórico de subcaracterísticas calculadas
    """
    queryset = SupportedSubCharacteristic.objects.prefetch_related('calculated_subcharacteristics')
    serializer_class = CalculatedSubCharacteristicHistorySerializer
