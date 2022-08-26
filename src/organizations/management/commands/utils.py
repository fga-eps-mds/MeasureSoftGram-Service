import contextlib
import datetime as dt
import random

from django.db.utils import IntegrityError
from django.utils import timezone

from characteristics.models import SupportedCharacteristic
from pre_configs.models import PreConfig
from subcharacteristics.models import SupportedSubCharacteristic
from utils import exceptions


def create_suported_characteristics(suported_characteristics):
    for characteristic in suported_characteristics:
        with contextlib.suppress(IntegrityError):
            klass = SupportedCharacteristic

            charact, _ = klass.objects.get_or_create(
                name=characteristic['name'],
                key=characteristic['key'],
            )

            subcharacteristics_keys = [
                subcharacteristic["key"]
                for subcharacteristic in characteristic["subcharacteristics"]
            ]

            subcharacteristics = SupportedSubCharacteristic.objects.filter(
                key__in=subcharacteristics_keys,
            )

            if subcharacteristics.count() != len(subcharacteristics_keys):
                raise exceptions.MissingSupportedSubCharacteristicError()

            charact.subcharacteristics.set(subcharacteristics)


def force_the_sum_to_equal_100(entities_data: dict):
    weight_sum = sum(entity['weight'] for entity in entities_data)

    if weight_sum != 100:
        entity = random.choice(entities_data)
        entity['weight'] += 100 - weight_sum

    return entities_data


def get_measures(subcharacteristic: SupportedSubCharacteristic):
    measures = subcharacteristic.measures.all()
    weight = 100 // measures.count()
    data = [{'key': measure.key, 'weight': weight} for measure in measures]
    data = force_the_sum_to_equal_100(data)
    return data


def get_subcharacteristics(characteristic: SupportedCharacteristic):
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
    characteristics = SupportedCharacteristic.objects.filter(
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

    preconfig = PreConfig.objects.create(
        name='custom pre-config',
        data=preconfig,
    )

    return preconfig


def get_random_start_at():
    return timezone.now() - dt.timedelta(days=random.randint(1, 90))


def get_random_end_at():
    return timezone.now() + dt.timedelta(days=random.randint(1, 90))


def get_random_changes(characteristics_keys):
    changes = []
    for _ in range(random.randint(5, 15)):
        changes.append({
            'characteristic_key': random.choice(characteristics_keys),
            'delta': random.randint(-50, 50),
        })
    return changes


def get_random_goal_data(pre_config: PreConfig):
    """
    Função que gera um objetivo aleatório com base na pré-configuração passada
    no parâmetro.
    """
    characteristics_keys = [
        obj["key"]
        for obj in pre_config.data['characteristics']
    ]

    major = random.randint(0, 9)
    minor = random.randint(0, 9)
    patch = random.randint(0, 9)

    return {
        'release_name': f'v{major}.{minor}.{patch}',
        'start_at': get_random_start_at(),
        'end_at': get_random_end_at(),
        "changes": get_random_changes(characteristics_keys),
    }
