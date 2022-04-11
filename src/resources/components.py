from flask_restful import Resource
from src.model.metrics_component_tree import MetricsComponentTree
from src.model.pre_config import PreConfig
from flask import request
import mongoengine as me
import requests


class ImportMetrics(Resource):
    def post(self):
        data = request.get_json(force=True)

        pre_configuration_id = data["pre_config_id"]

        try:
            if PreConfig.objects.with_id(pre_configuration_id) is None:
                return requests.codes.not_found
        except me.errors.ValidationError:
            return requests.codes.not_found

        MetricsComponentTree(
            pre_config_id=data.pop("pre_config_id"),
            components=data["components"]
        ).save()

        return requests.codes.created
