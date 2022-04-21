import mongoengine as me


class PreConfig(me.Document):
    name = me.StringField(unique=True, required=False, sparse=True)
    characteristics = me.DictField()
    subcharacteristics = me.DictField()
    measures = me.ListField()

    def created_at(self):
        return self.id.generation_time

    def to_json(self):
        return {
            "_id": str(self.pk),
            "name": self.name,
            "characteristics": self.characteristics,
            "subcharacteristics": self.subcharacteristics,
            "measures": self.measures,
            "created_at": str(self.created_at()),
        }
