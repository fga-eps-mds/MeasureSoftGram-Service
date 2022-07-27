from rest_framework import serializers

from service import models


class PreConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PreConfig
        fields = (
            'id',
            'name',
            'data',
            'created_at',
        )

    def validate(self, attrs):
        """
        Valida se a pré-configuração que está sendo criada é válida
        """
        if self.instance:
            raise ValueError("It's not allowed to edit a pre-configuration")

        models.PreConfig.validate_measures(
            attrs['data'],
        )

        models.PreConfig.validate_measures_weights(
            attrs['data'],
        )

        models.PreConfig.validate_subcharacteristics(
            attrs['data'],
        )

        models.PreConfig.validate_subcharacteristics_measures_relation(
            attrs['data'],
        )

        models.PreConfig.validate_subcharacteristics_weights(
            attrs['data'],
        )

        models.PreConfig.validate_characteristics(
            attrs['data'],
        )

        models.PreConfig.validate_characteristics_subcharacteristics_relation(
            attrs['data'],
        )

        models.PreConfig.validate_characteristics_weights(
            attrs['data'],
        )

        return attrs
