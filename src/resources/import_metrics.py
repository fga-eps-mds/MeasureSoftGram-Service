import requests
import mongoengine as me
from flask import request
from flask_restful import Resource
from src.model.pre_config import PreConfig
from src.resources.utils import simple_error_response
from src.model.metrics_component_tree import MetricsComponentTree


class ImportMetrics(Resource):
    def post(self):
        data = request.get_json(force=True)

        pre_configuration_id = data["pre_config_id"]

        try:
            if PreConfig.objects.with_id(pre_configuration_id) is None:
                return simple_error_response(
                    f"There is no pre configurations with ID {pre_configuration_id}",
                    requests.codes.not_found,
                    key="pre_config_id",
                )
        except me.errors.ValidationError:
            return simple_error_response(
                f"{pre_configuration_id} is not a valid ID",
                requests.codes.not_found,
                key="pre_config_id",
            )

        try:
            MetricsComponentTree(
                pre_config_id=data.pop("pre_config_id"),
                file_name=data.pop("file_name"),
                components=data["components"],
                language_extension=data["language_extension"],
            ).save()
        except me.errors.ValidationError as error:
            return error.to_dict(), requests.codes.unprocessable_entity

        return {}, requests.codes.created
