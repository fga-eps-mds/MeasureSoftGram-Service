import json
from flask import Flask, request, jsonify
import mongoengine as me


class PreConfig(me.Document):
    pre_config_name = me.StringField()
    caracteristcs = me.ListField()

    def to_json(self):
        return {
            "pre_config_name": self.pre_config_name,
            "caracteristcs": self.caracteristcs,
            "_id": str(self.pk),
        }
