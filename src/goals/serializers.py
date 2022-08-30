from rest_framework import serializers

from goals.models import Equalizer, Goal
from pre_configs.models import PreConfig


class CharacteristicDeltaSerializer(serializers.Serializer):
    """
    Exemplo:
    {
        "characteristic_key": "functional_suitability",
        "delta": 10,
    }
    """
    characteristic_key = serializers.CharField(max_length=255)
    delta = serializers.IntegerField()


class GoalSerializer(serializers.ModelSerializer):
    """
    Serializadora usada para serializar um Goal (meta).

    O campo changes é usado somente na criação de novos goals (metas)
    """
    changes = CharacteristicDeltaSerializer(many=True, write_only=True)
    data = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = (
            'id',
            'release_name',
            'start_at',
            'end_at',
            'changes',
            'data',
        )

    def get_data(self, obj):
        return obj.data

    def get_pre_config_characteristics(self):
        """
        Essa função retorna as características selecionadas na
        pré-configuração vigente.

        TODO: Essa função terá que mudar quando o sistema tiver mais de um
        repositório, pois será necessário fazer um fitro na tabela PreConfig
        pelo id do repositório.
        """
        pre_config = PreConfig.objects.first()
        return pre_config.get_characteristics_keys()

    def all_characteristics_are_defined_in_the_pre_config(self) -> bool:
        selected_characteristics_keys = set(
            self.get_pre_config_characteristics(),
        )
        changes = self.initial_data.get('changes', [])

        characteristics_keys = {
            change["characteristic_key"] for change in changes
        }

        issubset = characteristics_keys.issubset(
            selected_characteristics_keys,
        )

        return issubset

    def is_valid(self, raise_exception=False):
        valid_format = super().is_valid(raise_exception)

        issubset = self.all_characteristics_are_defined_in_the_pre_config()

        is_valid = valid_format and issubset

        if not is_valid and raise_exception:
            raise serializers.ValidationError((
                "It is not allowed to create goals with characteristics "
                "that were not selected in the pre-configuration."
            ))

        return is_valid

    def save(self, **kwargs):
        selected_characteristics_keys = self.get_pre_config_characteristics()

        equalizer = Equalizer(selected_characteristics_keys)

        data = self.validated_data
        changes = data.get('changes', [])

        for change in changes:
            equalizer.update(
                change["characteristic_key"],
                change["delta"],
            )

        self.validated_data.pop('changes')
        return super().save(data=equalizer.get_goal(), **kwargs)
