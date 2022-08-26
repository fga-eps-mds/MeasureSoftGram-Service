import contextlib
import random

from django.db.utils import IntegrityError

from service import models


def create_suported_characteristics(suported_characteristics):
    for characteristic in suported_characteristics:
        with contextlib.suppress(IntegrityError):
            klass = models.SupportedCharacteristic

            charact, _ = klass.objects.get_or_create(
                name=characteristic['name'],
                key=characteristic['key'],
            )

            subcharacteristics_keys = [
                subcharacteristic["key"]
                for subcharacteristic in characteristic["subcharacteristics"]
            ]

            subcharacteristics = models.SupportedSubCharacteristic.objects.filter(
                key__in=subcharacteristics_keys,
            )

            charact.subcharacteristics.set(subcharacteristics)


def force_the_sum_to_equal_100(entities_data: dict):
    weight_sum = sum(entity['weight'] for entity in entities_data)

    if weight_sum != 100:
        entity = random.choice(entities_data)
        entity['weight'] += 100 - weight_sum

    return entities_data


def get_measures(subcharacteristic: models.SupportedSubCharacteristic):
    measures = subcharacteristic.measures.all()
    weight = 100 // measures.count()
    data = [{'key': measure.key, 'weight': weight} for measure in measures]
    data = force_the_sum_to_equal_100(data)
    return data


def get_subcharacteristics(characteristic: models.SupportedCharacteristic):
    data = []

    subcharacteristics = characteristic.subcharacteristics.all()

    weight = 100 // subcharacteristics.count()

    for subcharacteristic in subcharacteristics:
        data.append({
            'key': subcharacteristic.key,
            'weight': weight,
            'measures': get_measures(subcharacteristic),
        })

    data = force_the_sum_to_equal_100(data)

    return data


def create_a_preconfig(characteristics_keys):
    """
    Função que gera uma pré-configuração com pesos divididos
    igualmente com base nas características passadas no parâmetro.

    Observação: A pré-configuração utiliza todoas as subcaracterísticas,
    medidas e métricas associadas com a arvore das características.
    """
    characteristics = models.SupportedCharacteristic.objects.filter(
        key__in=characteristics_keys,
    )

    weight = 100 // characteristics.count()

    data = []
    for characteristic in characteristics:
        data.append({
            'key': characteristic.key,
            'weight': weight,
            'subcharacteristics': get_subcharacteristics(characteristic),
        })

    data = force_the_sum_to_equal_100(data)
    preconfig = {'characteristics': data}

    preconfig = models.PreConfig.objects.create(
        name='custom pre-config',
        data=preconfig,
    )

    return preconfig
