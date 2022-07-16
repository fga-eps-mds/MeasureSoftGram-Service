from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import JSONParser


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def import_sonar_metrics(request):
    """
    Endpoint que recebe um o JSON obtido na API do SonarQube,
    extrai os valores das métricas contidas e salva no banco de dados.
    """

    data = dict(request.data)

    for metric_object in data['baseComponent']['measures']:
        print(metric_object['metric'])

    return Response()
