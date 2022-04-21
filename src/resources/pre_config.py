import requests
import mongoengine as me
from flask import request
from flask_restful import Resource
from src.model.pre_config import PreConfig


class PreConfigs(Resource):
    def post(self):
        data = request.get_json(force=True)

        try:
            pre_config = PreConfig(
                name=data.get("name", None),
                characteristics=data["characteristics"],
                subcharacteristics=data["subcharacteristics"],
                measures=data["measures"],
            )

            pre_config.save()
        except me.errors.NotUniqueError:
            return {
                "error": "The pre config name is already in use"
            }, requests.codes.unprocessable_entity

        return pre_config.to_json(), requests.codes.created
