from django.db import models


def is_the_same_call(prev_call: dict, current_call: dict):
    return (
        prev_call['name'] == current_call['name'] and
        prev_call['args'] == current_call['args'] and
        set(prev_call['kwargs']) == set(current_call['kwargs'])
    )


class CachedManager(models.Manager):
    """
    Esse cached manager foi feito pensando específicamente para as
    supported entities, pois essas tabelas mudam com quase nenhuma frequencia
    e são muito solicitadas.

    Usar esse cached manager com outras models certamente irá levar a bugs de
    difícil detecção. Como por exemplo queryset de filtros incorretos.
    """

    last_call = {'name': None, "args": None, "kwargs": None, "return": None}

    def filter(self, *args, **kwargs):
        call = {
            'name': 'filter',
            'args': args,
            'kwargs': kwargs,
        }
        if is_the_same_call(call, CachedManager.last_call):
            return self.last_call['return']

        qs = super().filter(*args, **kwargs)

        call['return'] = qs
        CachedManager.last_call = call

        return qs
