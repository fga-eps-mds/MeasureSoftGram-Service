from typing import Iterable, Set

from django.db import models

import utils


class SupportedSubCharacteristic(models.Model):
    """
    Classe que abstrai uma subcaracterística suportada pelo sistema.
    """
    name = models.CharField(max_length=128)
    key = models.CharField(max_length=128, unique=True)
    description = models.TextField(
        max_length=512,
        null=True,
        blank=True,
    )

    measures = models.ManyToManyField(
        'SupportedMeasure',
        related_name='related_subcharacteristics',
        blank=True,
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para validar se o campo `key` é valido
        """
        if not self.key:
            self.key = utils.namefy(self.name)
        super().save(*args, **kwargs)

    def has_unsupported_measures(
        self,
        measures_keys: Iterable[str],
    ) -> Set[str]:
        """
        Verifica se todas as medidas passadas no argumento `measures_keys`
        estão associadas a subcaracterística no modelo.

        Retorna um set com as medidas que não estão associadas
        a subcaracterística.
        """
        measures_keys = set(measures_keys)

        qs = self.measures.all()
        related_measures: Set[str] = set(qs.values_list('key', flat=True))

        return measures_keys - related_measures

    @staticmethod
    def has_unsupported_subcharacteristics(
        selected_subcharacteristics_keys: Iterable[str]
    ) -> Set[str]:
        """
        Verifica se existe alguma subcaracterística não suportada, e caso
        exista é retornado a lista das keys das subcaracterísticas
        não suportadas.
        """
        return utils.has_unsupported_entity(
            selected_subcharacteristics_keys,
            SupportedSubCharacteristic,
        )
