
import mongoengine as me


class Components(me.Document):

    pre_config_id = me.StringField()
    components_list = me.ListField()

    def to_json(self):
        return {"pre_config_id": self.pre_config_id,
                "components_list": self.components_list}
