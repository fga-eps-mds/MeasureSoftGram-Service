from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response


@api_view(['POST', 'HEAD', 'OPTIONS'])
@parser_classes([JSONParser])
def import_sonar_metrics(request):
    """
    Endpoint que recebe um o JSON obtido na API do SonarQube,
    extrai os valores das métricas contidas e salva no banco de dados.
    """
    data = dict(request.data)
    metrics = []

    for component in data['components']:
        obj = {}
        obj['qualifier'] = component['qualifier']
        obj['path'] = component['path']
        obj['metric'] = []

        for metric in component['measures']:
            obj['metric'].append({ 
                'metric': metric['metric'], 
                'value': float(metric['value'])
            })

        metrics.append(obj)

    return Response(metrics)
