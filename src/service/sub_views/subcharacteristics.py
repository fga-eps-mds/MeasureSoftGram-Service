from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

import utils
from service import clients, models, serializers


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def calculate_subcharacteristics(request):
    # 1. Get validated data
    serializer = serializers.SubcharacteristicsCalculationsRequestSerializer(
        data=request.data
    )
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # 2. get queryset
    subcharacteristics_keys = [
        subcharacteristic['key']
        for subcharacteristic in data['subcharacteristics']
    ]
    qs = models.SupportedSubCharacteristic.objects.filter(
        key__in=subcharacteristics_keys
    )

    pre_config = models.PreConfig.objects.first()

    # 3. get core json response
    core_params = {'subcharacteristics': []}
    subchar: models.SupportedSubcharacteristic

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

    response = clients.CoreClient().calculate_subcharacteristic(core_params)

    if response.ok is False:
        return Response(response.text, status=response.status_code)

    data = response.json()

    # 4. Save data
    calculated_values = {
        subcharacteristic['key']: subcharacteristic['value']
        for subcharacteristic in data['subcharacteristics']
    }

    calculated_subcharacteristics = []

    subchar: models.SupportedSubcharacteristic
    for subchar in qs:
        value = calculated_values[subchar.key]

        calculated_subcharacteristics.append(
            models.CalculatedSubCharacteristic(
                subcharacteristic=subchar,
                value=value,
            )
        )

    models.CalculatedSubCharacteristic.objects.bulk_create(
        calculated_subcharacteristics
    )

    # 5. Return data
    serializer = serializers.LatestCalculatedSubCharacteristicSerializer(
        qs,
        many=True,
    )

    return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupportedSubCharacteristicModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna todas as subcaracterísticas suportadas pelo sistema
    """
    queryset = models.SupportedSubCharacteristic.objects.all()
    serializer_class = serializers.SupportedSubCharacteristicSerializer


class LatestCalculatedSubCharacteristicModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o último valor calculado da subcaracterística
    """
    queryset = models.SupportedSubCharacteristic.objects.prefetch_related('calculated_subcharacteristics')
    serializer_class = serializers.LatestCalculatedSubCharacteristicSerializer


class CalculatedSubCharacteristicHistoryModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o histórico de subcaracterísticas calculadas
    """
    queryset = models.SupportedSubCharacteristic.objects.prefetch_related('calculated_subcharacteristics')
    serializer_class = serializers.CalculatedSubCharacteristicHistorySerializer
