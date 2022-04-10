from flask_restful import Resource
from src.model.component import Components
from src.model.pre_config import PreConfig
from flask import request
import mongoengine as me


class PreConfigComponents(Resource):
    def post(self):

        data = request.get_json(force=True)

        pre_configuration_id = data["pre_config_id"]

        try:
            if PreConfig.objects.with_id(pre_configuration_id) is None:
                return 404
            Components(
                pre_config_id=data.pop("pre_config_id"),
                components_list=data["components"]
            ).save()
            return 201
        except me.errors.ValidationError:
            return 404
