from rest_framework import serializers

from service import models
from utils.exceptions import InvalidPreConfigException


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

        data = attrs['data']

        try:
            models.PreConfig.validate_measures(data)
            models.PreConfig.validate_measures_weights(data)
            models.PreConfig.validate_subcharacteristics(data)
            models.PreConfig.validate_subcharacteristics_measures_relation(data)
            models.PreConfig.validate_subcharacteristics_weights(data)
            models.PreConfig.validate_characteristics(data)
            models.PreConfig.validate_characteristics_subcharacteristics_relation(data)
            models.PreConfig.validate_characteristics_weights(data)
            models.PreConfig.same_as_current_preconfig(data)

        except InvalidPreConfigException as exc:
            raise serializers.ValidationError(exc) from exc

        return attrs
