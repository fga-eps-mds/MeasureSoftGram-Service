from rest_framework import serializers

from pre_configs.models import PreConfig
from utils.exceptions import InvalidPreConfigException


class PreConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreConfig
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
            PreConfig.validate_measures(data)
            PreConfig.validate_measures_weights(data)
            PreConfig.validate_subcharacteristics(data)
            PreConfig.validate_subcharacteristics_measures_relation(data)
            PreConfig.validate_subcharacteristics_weights(data)
            PreConfig.validate_characteristics(data)
            PreConfig.validate_characteristics_subcharacteristics_relation(data)
            PreConfig.validate_characteristics_weights(data)
            PreConfig.is_different_than_the_current_preconfig(data)

        except InvalidPreConfigException as exc:
            raise serializers.ValidationError(exc) from exc

        return attrs
