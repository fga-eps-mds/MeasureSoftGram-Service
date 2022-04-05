from flask_restful import Resource
from src.model.metric import Metrics
from src.model.pre_config import PreConfig
from flask import Flask, request, jsonify


class PreConfigMetrics(Resource):
    def post(self):

        data = request.get_json(force=True)

        id_wanted = data["id_wanted"]

        if PreConfig.objects(_id=id_wanted) == {}:
            print("Id not found!")
        else:
            print("Id founded!")

        pre_config_metrics = Metrics()

        pre_config_metrics.comment_lines_density = data["comment_lines_density"]
        pre_config_metrics.complexity = data["complexity"]
        pre_config_metrics.coverage = data["coverage"]
        pre_config_metrics.duplicated_lines_density = data["duplicated_lines_density"]
        pre_config_metrics.files = data["files"]
        pre_config_metrics.functions = data["functions"]
        pre_config_metrics.ncloc = data["ncloc"]
        pre_config_metrics.security_rating = data["security_rating"]
        pre_config_metrics.test_errors = data["test_errors"]
        pre_config_metrics.test_execution_time = data["test_execution_time"]
        pre_config_metrics.test_failures = data["test_failures"]
        pre_config_metrics.tests = data["tests"]

        pre_config_metrics.save()

        return pre_config_metrics.to_json(), 201