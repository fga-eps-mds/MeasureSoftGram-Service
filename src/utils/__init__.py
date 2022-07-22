import datetime as dt
import random
import string

from django.utils import timezone

from utils import exceptions

from itertools import zip_longest

def chunkify(iterable, n, fillvalue=None) -> list:
    args = [iter(iterable)] * n
    return list(zip_longest(*args, fillvalue=fillvalue))


def get_random_datetime(start_date, end_date):
    return timezone.make_aware(
        dt.datetime.fromtimestamp(
            random.randint(
                int(start_date.timestamp()),
                int(end_date.timestamp()),
            )
        )
    )


def namefy(str):
    return str.replace('_', ' ').title()


def get_random_string():
    r = random.choice(string.ascii_uppercase + string.digits)
    return ''.join(r for _ in range(100))


def get_random_qualifier():
    return random.choice(['UTS', 'FIL', 'DIR'])


def get_random_value(metric_type):
    if metric_type == 'INT':
        return random.randint(0, 100)

    elif metric_type == 'FLOAT':
        # Para valores aleatórios entre 0 e 100
        # return random.random() * random.randint(0, 100)

        # Para valores variando perto de 50
        return random.uniform(0, 100)

    elif metric_type == 'PERCENT':
        return random.random()

    elif metric_type == 'BOOL':
        return random.choice([True, False])

    elif metric_type == 'STRING':
        # Por mais que o tipo seja uma string, o valor da única
        # métrica que tem esse tipo no sonarqube é a métrica
        # `new_development_cost` cujo valor é um float
        return random.uniform(0, 1000)

    elif metric_type == 'DATA':
        return random.randint(0, 100)

    elif metric_type == 'WORK_DUR':
        return random.randint(0, 100)

    elif metric_type == 'DISTRIB':
        return random.randint(0, 100)

    elif metric_type == 'RATING':
        return random.randint(0, 100)

    elif metric_type == 'LEVEL':
        return random.choice([True, False])

    elif metric_type == 'MILLISEC':
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=90)
        datetime = get_random_datetime(start_date, end_date)
        return datetime.timestamp()

    raise exceptions.RandomMetricTypeException(
        'Metric type not supported'
    )


class DateRange:
    def __init__(self, start: dt.date, end: dt.date):
        self.start = start
        self.end = end

    def __str__(self):
        return f"{self.start} - {self.end}"

    def __repr__(self):
        return f"{self.start} - {self.end}"