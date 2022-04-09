from flask_restful import Resource
from src.model.metric import Metrics
from src.model.pre_config import PreConfig
from flask import request


class PreConfigMetrics(Resource):
    def post(self):

        data = request.get_json(force=True)

        pre_config_id = data["pre_config_id"]

        try:
            if PreConfig.objects.with_id(pre_config_id) == None:
                return 404
            else:
                data.pop("pre_config_id", None)
                Metrics(metrics_list=data).save()
                return 201
        except Exception as InvalidQueryError:
            return 404
