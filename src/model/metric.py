
import mongoengine as me


class Metrics(me.Document):

    metrics_list = me.DictField()

    def to_json(self):
        return {"metrics_list": self.metrics_list}
