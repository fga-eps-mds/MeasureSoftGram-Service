from rest_framework import serializers

from pre_configs.models import PreConfig
from utils.exceptions import InvalidPreConfigException


class PreConfigSerializer(serializers.ModelSerializer):
    created_config = serializers.SerializerMethodField('has_created_config')

    class Meta:
        model = PreConfig
        fields = (
            'id',
            'name',
            'data',
            'created_at',
            'created_config'
        )
        extra_kwargs = {
            'created_at': {'read_only': True},
            'created_config': {'read_only': True, }
        }

    def has_created_config(self, obj):
        return len(PreConfig.objects.values('id')) > 1

    def validate(self, attrs):
        """
        Valida se a pré-configuração que está sendo criada é válida
        """
        if self.instance:
            raise ValueError("It's not allowed to edit a pre-configuration")

        data = attrs["data"]

        try:
            PreConfig.validate_measures(data)
            PreConfig.validate_measures_weights(data)
            PreConfig.validate_subcharacteristics(data)
            PreConfig.validate_subcharacteristics_measures_relation(data)
            PreConfig.validate_subcharacteristics_weights(data)
            PreConfig.validate_characteristics(data)
            PreConfig.validate_characteristics_subcharacteristics_relation(data)
            PreConfig.validate_characteristics_weights(data)

            product = self.context["view"].get_product()
            current_preconfig = product.pre_configs.first()

            PreConfig.is_different_than_the_current_preconfig(
                data,
                current_preconfig,
            )

        except InvalidPreConfigException as exc:
            raise serializers.ValidationError(exc) from exc

        return attrs
