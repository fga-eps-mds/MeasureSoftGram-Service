from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status

from service import models
from service import clients
from service import serializers


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def calculate_measures(request):
    """
    Calcula uma medida
    """
    # 1. Valida se os dados foram enviados corretamente
    serializer = serializers.MeasuresCalculationsRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # 2. Obtenção das medidas suportadas pelo serviço
    measure_keys = [measure['key'] for measure in data['measures']]
    qs = models.SupportedMeasure.objects.filter(key__in=measure_keys)

    # 3. Criação do dicionário que será enviado para o serviço `core`
    core_params = {'measures': []}

    # 4. Obtenção das métricas necessárias para calcular as medidas
    measure: models.SupportedMeasure
    for measure in qs:
        metric_params = measure.get_latest_metric_params()

        core_params['measures'].append({
            'key': measure.key,
            'parameters': metric_params,
        })

    # 5. Solicitação do cáculo ao serviço core
    # TODO: Se alguma métrica ter sido recentemente calculada não recalculá-la
    response = clients.CoreClient().calculate_measure(core_params)

    if response.ok is False:
        return Response(response.text, status=response.status_code)

    data = response.json()

    calculated_values = {
        measure['key']: measure['value']
        for measure in data['measures']
    }

    # 6. Salvando no banco de dados as medidas calculadas
    measure: models.SupportedMeasure
    for measure in qs:
        value = calculated_values[measure.key]
        measure.calculated_measures.create(value=value)

    # 7. Retornando o resultado
    serializer = serializers.LatestMeasuresCalculationsRequestSerializer(
        qs,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )
