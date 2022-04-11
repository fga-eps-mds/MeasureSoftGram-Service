import mongoengine as me
import requests
from src.util.constants import CORE_URL


class MetricsComponentTree(me.Document):

    pre_config_id = me.StringField()
    components = me.ListField()

    def clean(self):
        available_entries = requests.get(
            CORE_URL + "/available-pre-configs",
            headers={"Accept": "application/json"},
        ).json()

        # Reduzir todas as metricas necessárias para a pré config relacionada em um vetor
        # PreConfig.with_id(self.pre_config_id)
        all_metrics = [
            key for key in available_entries["measures"].keys()
        ]

        [key for key in {"name": "asd", "age": 12}.keys()]

        all_metrics

        # A partir do vetor verificar se existe ao menos um component que possua
        # a métrica em questão

        raise me.errors.ValidationError(
            "The metrics in this file are not the expected in the pre config"
        )

    def to_json(self):
        return {"pre_config_id": self.pre_config_id, "components": self.components}
