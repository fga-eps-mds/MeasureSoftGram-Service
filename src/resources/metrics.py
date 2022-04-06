from flask_restful import Resource
from src.model.metric import Metrics
from src.model.pre_config import PreConfig
from flask import Flask, request, jsonify
from src.exceptions import IdNotFoundedException


class PreConfigMetrics(Resource):
    def post(self):

        data = request.get_json(force=True)

        id_wanted = data["id_wanted"]

        if PreConfig.objects(_id=id_wanted) == {}:
            raise IdNotFoundedException()
        else:
            data.pop("id_wanted", None)
            pre_config_metrics = Metrics()
            pre_config_metrics.metrics_list = data

            pre_config_metrics.save()
            return pre_config_metrics.to_json(), 201
