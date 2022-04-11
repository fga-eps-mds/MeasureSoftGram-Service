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

        pre_config = PreConfig.objects.with_id(self.pre_config_id)

        found_metrics = []
        missing_metrics = []
        required_metrics = []

        for measure in pre_config.measures:
            for metric in available_entries["measures"][measure]["metrics"]:
                required_metrics.append(metric)

        all_metrics = list(
            map(
                lambda item: list(map(lambda itm: itm["metric"], item["measures"])),
                self.components,
            )
        )

        found_metrics = dict.fromkeys(
            [item for sublist in all_metrics for item in sublist], True
        )

        for required_metric in required_metrics:
            if not found_metrics.get(required_metric, False):
                missing_metrics.append(required_metric)

        if len(missing_metrics) > 0:
            missing_text = ", ".join(missing_metrics)

            raise me.errors.ValidationError(
                "The metrics in this file are not the expected in the pre config."
                + f"Missing metrics: {missing_text}."
            )

    def to_json(self):
        return {"pre_config_id": self.pre_config_id, "components": self.components}
