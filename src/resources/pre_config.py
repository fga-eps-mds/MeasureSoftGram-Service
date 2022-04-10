from flask import request
from flask_restful import Resource
from src.model.pre_config import PreConfig
import requests
import mongoengine as me


class PreConfigs(Resource):
    def get(self):
        return PreConfig.objects().to_json(), 200

    def post(self):
        data = request.get_json(force=True)

        try:
            pre_config = PreConfig(
                name=data["name"],
                characteristics=data["characteristics"],
                subcharacteristics=data["subcharacteristics"],
                measures=data["measures"],
                characteristics_weights=data["characteristics_weights"],
                subcharacteristics_weights=data["subcharacteristics_weights"],
                measures_weights=data["measures_weights"],
            ).save()
        except me.errors.NotUniqueError:
            return {
                "error": "The pre config name is already in use"
            }, requests.codes.unprocessable_entity

        return pre_config.to_json(), requests.codes.created
