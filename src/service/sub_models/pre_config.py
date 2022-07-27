from django.db import models
from django.utils import timezone

from service.sub_models.measures import SupportedMeasure
from service.sub_models.subcharacteristics import SupportedSubCharacteristic
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
        Sobrescreve o método save para validar se a pré-configuração que
        está sendo criada ou editada é ou não válida
        """
        if self.id:
            raise ValueError("It's not allowed to edit a pre-configuration")

        self.validate_measures(self.data)
        self.validate_measures_weights(self.data)

        self.validate_subcharacteristics(self.data)
        self.validate_subcharacteristics_measures_relation(self.data)
        self.validate_subcharacteristics_weights(self.data)

        self.validate_characteristics(self.data)
        self.validate_characteristics_subcharacteristics_relation(self.data)
        self.validate_characteristics_weights(self.data)

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
    def validate_measures_weights(data: dict):
        """
        Verifica se o somatório do peso das medidas é igual a 100

        Raises a `ValueError` caso alguma weight não seja
        """
        for characteristic in data['characteristics']:
            for subcharacteristic in characteristic['subcharacteristics']:

                sum_of_weights: int = sum(
                    measure['weight']
                    for measure in subcharacteristic['measures']
                )

                if sum_of_weights != 100:
                    raise ValueError((
                        "The sum of weights of measures of subcharacteristic "
                        f"`{subcharacteristic['key']}` is not 100"
                    ))

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
    def validate_subcharacteristics_measures_relation(data: dict):
        """
        Valida se as medidas que estão relacionadas com as subcaracteristicas
        na pré-configuração são realmente relacionadas com as
        subcaracteristicas no modelo

        Raises a `ValueError` caso alguma medida não seja relacionada
        """

        for characteristic in data['characteristics']:
            for subcharacteristic in characteristic['subcharacteristics']:

                subchar = SupportedSubCharacteristic.objects.get(
                    key=subcharacteristic['key'],
                )

                sub_measures = {
                    measure['key']
                    for measure in subcharacteristic['measures']
                }

                if invalid_measures := subchar.has_unsupported_measures(sub_measures):

                    invalid_measures: list = [f"`{key}`" for key in invalid_measures]
                    invalid_measures: str = ', '.join(invalid_measures)

                    raise ValueError((
                        "Failed to save pre-config. It is not allowed to "
                        f"associate the measures [{invalid_measures}] with the "
                        f"subcharacteristic {subchar.key}"
                    ))

    @staticmethod
    def validate_subcharacteristics_weights(data: dict):
        """
        Verifica se o somatório do peso das subcharacteristics é igual a 100

        Raises a `ValueError` caso alguma weight não seja
        """
        for characteristic in data['characteristics']:
            sum_of_weights: int = sum(
                subcharacteristic['weight']
                for subcharacteristic in characteristic['subcharacteristics']
            )

            if sum_of_weights != 100:
                raise ValueError((
                    "The sum of weights of subcharacteristics of "
                    f"characteristic `{characteristic['key']}` is not 100"
                ))

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
        )

        if unsuported:
            raise ValueError(
                f"The following characteristics are not supported: {unsuported}"
            )

    @staticmethod
    def validate_characteristics_subcharacteristics_relation(data: dict):
        """
        Valida se as subcharacteristics que estão relacionadas com as
        characteristics na pré-configuração são realmente relacionadas com as
        characteristics no modelo

        Raises a `ValueError` caso alguma subcharacteristic não seja
        """

        for characteristic in data['characteristics']:
            charact = SupportedCharacteristic.objects.get(
                key=characteristic['key'],
            )

            charact_subcharacteristics = {
                subcharacteristic['key']
                for subcharacteristic in characteristic['subcharacteristics']
            }

            if invalid_subs := charact.has_unsupported_subcharacteristics(
                charact_subcharacteristics,
            ):
                invalid_subs: list = [f"`{key}`" for key in invalid_subs]
                invalid_subs: str = ', '.join(invalid_subs)

                raise ValueError((
                    "Failed to save pre-config. It is not allowed to "
                    f"associate the subcharacteristics [{invalid_subs}] "
                    f"with the characteristic {charact.key}"
                ))

    @staticmethod
    def validate_characteristics_weights(data: dict):
        """
        Verifica se o somatório do peso das characteristics é igual a 100

        Raises a `ValueError` caso alguma weight não seja
        """
        sum_of_weights: int = sum(
            characteristic['weight']
            for characteristic in data['characteristics']
        )

        if sum_of_weights != 100:
            raise ValueError("The sum of weights of characteristics is not 100")
