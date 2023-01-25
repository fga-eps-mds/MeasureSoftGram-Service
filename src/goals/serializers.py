from rest_framework import serializers

from characteristics.models import CalculatedCharacteristic
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


class AllGoalsSerializer(serializers.ModelSerializer):
    goal = serializers.SerializerMethodField()
    accomplished = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = (
            'id',
            'release_name',
            'start_at',
            'created_by',
            'end_at',
            'goal',
            'accomplished'
        )

    def get_goal(self, obj):
        return obj.data

    def get_accomplished(self, obj):
        # FIXME: Estamos pegando apenas as 2 primeiras, pois o mesmo
        # produto pode ter várias características calculadas
        chars = CalculatedCharacteristic.objects.filter(
            repository__product=obj.product,
            created_at__gte=obj.start_at,
            created_at__lte=obj.end_at
        ).values(
            'characteristic__key', 'value'
        ).order_by('characteristic__id').distinct('characteristic__id')
        return {char['characteristic__key']: char['value'] for char in chars}


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
        product = self.get_product()
        pre_config = product.pre_configs.first()
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

    def check_if_all_characteristics_are_defined_in_the_pre_config(
        self,
        valid_format=True,
        raise_exception=False,
    ):
        issubset = self.all_characteristics_are_defined_in_the_pre_config()

        is_valid = valid_format and issubset

        if not is_valid and raise_exception:
            raise serializers.ValidationError((
                "It is not allowed to create goals with characteristics "
                "that were not selected in the pre-configuration."
            ))

        return is_valid

    def get_product(self):
        product = None

        if view := self.context.get('view', None):
            product = view.get_product()

        return product

    def check_if_it_is_the_same_as_the_current_goal(
        self,
        valid_format=True,
        raise_exception=False,
    ):
        product = self.get_product()
        current_goal = product.goals.first()

        if not current_goal:
            return True

        start_at: str = current_goal.start_at.strftime('%Y-%m-%d')
        end_at: str = current_goal.end_at.strftime('%Y-%m-%d')
        data: dict = self.changes_to_data()

        is_the_same = (
            current_goal.release_name == self.initial_data.get('release_name')
            and start_at == self.initial_data.get('start_at')
            and end_at == self.initial_data.get('end_at')
            and current_goal.data == data
        )

        if is_the_same and raise_exception:
            raise serializers.ValidationError((
                "It is not allowed to create goals that are the same as the "
                "current goal."
            ))

        is_valid = not is_the_same
        return is_valid and valid_format

    def is_valid(self, raise_exception=False):
        valid_format = super().is_valid(raise_exception)

        is_valid_1 = self.check_if_all_characteristics_are_defined_in_the_pre_config(
            valid_format=valid_format,
            raise_exception=raise_exception,
        )

        is_valid_2 = self.check_if_it_is_the_same_as_the_current_goal(
            valid_format=valid_format,
            raise_exception=raise_exception,
        )

        if not (is_valid_1 and is_valid_2) and raise_exception:
            raise serializers.ValidationError("The goal is not valid.")

        return is_valid_1 and is_valid_2

    def changes_to_data(self):
        """
        Essa função converte o campo changes para o formato de dados
        """
        selected_characteristics_keys = self.get_pre_config_characteristics()
        equalizer = Equalizer(selected_characteristics_keys)

        data = self.validated_data
        changes = data.get('changes', [])

        for change in changes:
            equalizer.update(
                change["characteristic_key"],
                change["delta"],
            )

        return equalizer.get_goal()

    def save(self, **kwargs):
        data = self.changes_to_data()
        self.validated_data.pop('changes')
        return super().save(data=data, **kwargs)
