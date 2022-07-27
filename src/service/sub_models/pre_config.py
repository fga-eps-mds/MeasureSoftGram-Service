from typing import Callable, Iterable, Set
from django.db import models
from django.utils import timezone

from service.sub_models.measures import SupportedMeasure

from service.sub_models.subcharacteristics import (
    SupportedSubCharacteristic,
)

from service.sub_models.characteristics import SupportedCharacteristic

import utils


class PreConfig(models.Model):
    """
    Classe que abstrai uma pré-configuração do modelo.

    Nessa tabela será armazenado todas as pré-configurações criadas do modelo,
    sendo que a última pré-configuração é sempre a vigente. Ou seja, as tuplas
    dessa tabela não devem ser editadas ou apagadas, somente adicionadas novas
    """
    class Meta:
        # Aqui estamos ordenando na ordem decrescente, ou seja, nos
        # querysets os registros mais recentes vem
        # primeiro (qs.first() == mais recente)
        ordering = ['-created_at']

    created_at = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=128, null=True, blank=True)
    data = models.JSONField()

    def __str__(self):
        return f'ID: {self.id}, Name: {self.name}'

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para validar se o campo `data` é valido
        """
        self.validate_measures(self.data)
        self.validate_subcharacteristics(self.data)
        self.validate_characteristics(self.data)
        super().save(*args, **kwargs)

    @staticmethod
    def validate_measures(data: dict):
        """
        Verifica se as medidas contidas no dicionário `data` são suportadas.

        Raises a `ValueError` caso alguma medida não seja suportada.
        """
        selected_measures_set = set()

        for characteristic in data['characteristics']:
            for subcharacteristic in characteristic['subcharacteristics']:
                for measure in subcharacteristic['measures']:
                    measure_key = measure['key']
                    selected_measures_set.add(measure_key)

        unsuported: str = utils.validate_entity(
            selected_measures_set,
            SupportedMeasure.has_unsupported_measures,
        )

        if unsuported:
            raise ValueError(
                f"The following measures are not supported: {unsuported}"
            )

    @staticmethod
    def validate_subcharacteristics(data: dict):
        """
        Verifica se as subcharacteristics contidas no dicionário `data` são
        suportadas

        Raises a `ValueError` caso alguma subcharacteristic não seja
        """
        selected_subcharacteristics_set = set()

        for characteristic in data['characteristics']:
            for subcharacteristic in characteristic['subcharacteristics']:
                subcharacteristic_key = subcharacteristic['key']
                selected_subcharacteristics_set.add(subcharacteristic_key)

        unsuported: str = utils.validate_entity(
            selected_subcharacteristics_set,
            SupportedSubCharacteristic.has_unsupported_subcharacteristics,
        )

        if unsuported:
            raise ValueError(
                f"The following subcharacteristics are not supported: {unsuported}"
            )

    @staticmethod
    def validate_characteristics(data: dict):
        """
        Verifica se as characteristics contidas no dicionário `data` são
        suportadas

        Raises a `ValueError` caso alguma characteristic não seja
        """
        selected_characteristics_set = set()

        for characteristic in data['characteristics']:
            characteristic_key = characteristic['key']
            selected_characteristics_set.add(characteristic_key)

        unsuported:str = utils.validate_entity(
            selected_characteristics_set,
            SupportedCharacteristic.has_unsupported_characteristics,
            'characteristics',
        )

        if unsuported:
            raise ValueError(
                f"The following characteristics are not supported: {unsuported}"
            )
