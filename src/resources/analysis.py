from flask_restful import Resource
from flask import request
from src.model.pre_config import PreConfig
from src.model.metrics_component_tree import MetricsComponentTree
from flask import jsonify


class Analysis(Resource):
    def post(self):
        data = request.get_json(force=True)

        pre_config = PreConfig.objects.with_id(data["pre_config_id"])

        components = MetricsComponentTree.objects(pre_config_id=data["pre_config_id"])

        return jsonify({"pre_config": pre_config, "components": components})
