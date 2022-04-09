
import mongoengine as me


class Metrics(me.Document):

    pre_config_id = me.StringField()
    metrics_list = me.DictField()

    def to_json(self):
        return {"pre_config_id": self.pre_config_id,
                "metrics_list": self.metrics_list}
