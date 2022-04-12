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
                return {
                    "pre_config_id": f"There is no pre configurations with ID {pre_configuration_id}"
                }, requests.codes.not_found
        except me.errors.ValidationError:
            return {
                "pre_config_id": f"{pre_configuration_id} is not a valid ID"
            }, requests.codes.not_found

        try:
            MetricsComponentTree(
                pre_config_id=data.pop("pre_config_id"), components=data["components"]
            ).save()
        except me.errors.ValidationError as error:
            return error.to_dict(), requests.codes.unprocessable_entity

        return {}, requests.codes.created
