import json
from flask import Flask, request, jsonify
import mongoengine as me


class PreConfig(me.Document):
    name = me.StringField(unique=True)
    characteristics = me.ListField()
    subcharacteristics = me.ListField()
    measures = me.ListField()
    characteristics_weights = me.ListField()
    subcharacteristics_weights = me.ListField()
    measures_weights = me.ListField()

    def created_at(self):
        return self.id.generation_time

    def to_json(self):
        return {
            "_id": str(self.pk),
            "name": self.name,
            "characteristics": self.characteristics,
            "subcharacteristics": self.subcharacteristics,
            "measures": self.measures,
            "characteristics_weights": self.characteristics_weights,
            "subcharacteristics_weights": self.subcharacteristics_weights,
            "measures_weights": self.measures_weights,
            "created_at": self.created_at(),
        }
