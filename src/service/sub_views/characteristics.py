from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

import utils
from service import clients, models, serializers


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def calculate_characteristics(request):
    # 1. Get validated data
    serializer = serializers.CharacteristicsCalculationsRequestSerializer(
        data=request.data
    )
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # 2. Get queryset
    characteristics_keys = [
        characteristic['key']
        for characteristic in data['characteristics']
    ]
    qs = models.SupportedCharacteristic.objects.filter(
        key__in=characteristics_keys
    )

    # 3. Create Core request
    pre_config = models.PreConfig.objects.first()

    core_params = {'characteristics': []}

    char: models.SupportedCharacteristic
    for char in qs:
        try:
            subchars_params = char.get_latest_subcharacteristics_params(
                pre_config,
            )

        except utils.exceptions.SubCharacteristicNotDefinedInPreConfiguration as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        core_params['characteristics'].append({
            'key': char.key,
            'subcharacteristics': subchars_params,
        })

    response = clients.CoreClient.calculate_characteristic(core_params)

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
            models.CalculatedCharacteristic(
                characteristic=characteristic,
                value=value,
            )
        )

    models.CalculatedCharacteristic.objects.bulk_create(
        calculated_characteristics,
    )

    # 6. Retornando o resultado
    serializer = serializers.LatestCalculatedCharacteristicSerializer(
        qs,
        many=True,
    )

    return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupportedCharacteristicModelViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Viewset que retorna todas as características suportadas pelo sistema
    """
    queryset = models.SupportedCharacteristic.objects.all()
    serializer_class = serializers.SupportedCharacteristicSerializer


class LatestCalculatedCharacteristicModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o último valor calculado da característica
    """
    queryset = models.SupportedCharacteristic.objects.prefetch_related(
        'calculated_characteristics'
    )
    serializer_class = serializers.LatestCalculatedCharacteristicSerializer


class CalculatedCharacteristicHistoryModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet para recuperar o histórico de características calculadas
    """
    queryset = models.SupportedCharacteristic.objects.prefetch_related(
        'calculated_characteristics'
    )
    serializer_class = serializers.CalculatedCharacteristicHistorySerializer
