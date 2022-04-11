import mongoengine as me
import requests
from src.util.constants import CORE_URL
from src.model.pre_config import PreConfig


class MetricsComponentTree(me.Document):

    pre_config_id = me.StringField()
    components = me.ListField()

    def clean(self):
        available_entries = requests.get(
            CORE_URL + "/available-pre-configs",
            headers={"Accept": "application/json"},
        ).json()

        # Reduzir todas as metricas necessárias para a pré config relacionada em um vetor
        pre_config = PreConfig.objects.with_id(self.pre_config_id)

        found_metrics = []
        required_metrics = []

        for measure in pre_config.measures:
            for metric in available_entries["measures"][measure]["metrics"]:
                required_metrics.append(metric)

        # A partir do vetor verificar se existe ao menos um component que possua
        # a métrica em questão
        for required_metric in required_metrics:
            for component in self.components:
                for measure in component["measures"]:
                    found = measure["metric"] == required_metric

                    if found:
                        break

                if found:
                    break

            found_metrics.append(found)

        if not all(found_metrics):
            msg = "Missing metrics: "

            for idx in range(len(found_metrics)):
                if not found_metrics[idx]:
                    msg = f"{msg} {required_metrics[idx]},"

            raise me.errors.ValidationError(
                f"The metrics in this file are not the expected in the pre config. {msg[:-1]}"
            )

    def to_json(self):
        return {"pre_config_id": self.pre_config_id, "components": self.components}
