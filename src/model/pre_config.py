import json
from flask import Flask, request, jsonify
import mongoengine as me


class PreConfig(me.Document):
    name = me.StringField()
    characteristics = me.ListField()

    def to_json(self):
        return {
            "name": self.name,
            "characteristics": self.characteristics,
            "_id": str(self.pk),
        }
