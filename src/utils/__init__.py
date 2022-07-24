import datetime as dt
import random
import string
from itertools import zip_longest

from django.utils import timezone

from utils import exceptions


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
    "Key to name"
    return str.replace('_', ' ').title()


def keyfy(str):
    "Name to key"
    return str.replace(' ', '_').lower()


def get_random_string():
    r = random.choice(string.ascii_uppercase + string.digits)
    return ''.join(r for _ in range(100))


def get_random_qualifier():
    return random.choice(['UTS', 'FIL', 'DIR'])

def get_random_value(metric_type): # noqa: max-complexity: 13
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
    def __init__(self, start: dt.datetime, end: dt.datetime):
        if not isinstance(start, dt.datetime):
            raise TypeError('start must be a datetime.date')

        if not isinstance(end, dt.datetime):
            raise TypeError('end must be a datetime.date')

        self.start = start
        self.end = end

    @staticmethod
    def create_from_today(days: int):
        return DateRange(
            start=dt.datetime.today() - dt.timedelta(days=days),
            end=dt.datetime.today(),
        )

    def __str__(self):
        return f"{self.start} - {self.end}"

    def __repr__(self):
        return f"{self.start} - {self.end}"
