import mongoengine as me
import requests
from src.util.constants import CORE_URL
from src.model.pre_config import PreConfig


def flatten_list(array):
    return [item for sublist in array for item in sublist]


def get_required_metrics(pre_config_id):
    available_entries = requests.get(
        CORE_URL + "/available-pre-configs",
        headers={"Accept": "application/json"},
    ).json()

    pre_config = PreConfig.objects.with_id(pre_config_id)

    required_metrics = []

    for measure in pre_config.measures:
        for metric in available_entries["measures"][measure]["metrics"]:
            required_metrics.append(metric)

    return list(dict.fromkeys(required_metrics))


class MetricsComponentTree(me.Document):

    pre_config_id = me.StringField()
    file_name = me.StringField()
    components = me.ListField()
    language_extension = me.StringField()

    def clean(self):
        found_metrics = []
        missing_metrics = []
        required_metrics = get_required_metrics(self.pre_config_id)

        all_file_metrics = list(
            map(
                lambda item: list(map(lambda itm: itm["metric"], item["measures"])),
                self.components,
            )
        )

        found_metrics = dict.fromkeys(flatten_list(all_file_metrics), True)

        for required_metric in required_metrics:
            if not found_metrics.get(required_metric, False):
                missing_metrics.append(required_metric)

        if len(missing_metrics) > 0:
            missing_text = ", ".join(missing_metrics)

            raise me.errors.ValidationError(
                "The metrics in this file are not the expected in the pre config."
                + f" Missing metrics: {missing_text}."
            )

    def to_json(self):
        return {
            "pre_config_id": self.pre_config_id,
            "file_name": self.file_name,
            "components": self.components,
            "language_extension": self.language_extension,
        }
