from flask import request
from flask_restful import Resource
from src.model.pre_config import PreConfig
import requests
import mongoengine as me


class PreConfigs(Resource):
    def get(self):
        # return PreConfig.objects.to_json(), 200
        return PreConfig.objects.with_id("625439e55742575d765b3c22").to_json(), 200

    def post(self):
        data = request.get_json(force=True)

        try:
            pre_config = PreConfig(**data).save()
        except me.errors.NotUniqueError:
            return {
                "error": "The pre config name is already in use"
            }, requests.codes.unprocessable_entity

        return pre_config.to_json(), requests.codes.created
