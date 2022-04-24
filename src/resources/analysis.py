from cgi import print_form
from flask_restful import Resource
from flask import request
from src.model.pre_config import PreConfig
from src.model.analysis import AnalysisComponents
from src.model.metrics_component_tree import MetricsComponentTree
from flask import jsonify
import requests
import json
from src.util.constants import CORE_URL
import mongoengine as me


class Analysis(Resource):
    def post(self):
        data = request.get_json(force=True)

        pre_configuration_id = data["pre_config_id"]

        pre_config = PreConfig.objects.with_id(pre_configuration_id)

        if pre_config is None:
            return {
                "error": f"There is no pre configurations with ID {pre_configuration_id}"
            }, requests.codes.not_found

        components = MetricsComponentTree.objects(
            pre_config_id=data["pre_config_id"]
        ).first()

        if components is None:
            return {
                "error": f"There is no metrics file associated with this pre config {pre_configuration_id}"
            }, requests.codes.not_found

        analysis = AnalysisComponents.objects(
            pre_config_id=pre_configuration_id
        ).first()

        if analysis is not None:
            # Analysis is already done

            analysis_json = analysis.to_json()

            return {
                "pre_config": pre_config.to_json(),
                "components": components.to_json(),
                "analysis": {
                    "sqc": analysis_json["sqc"],
                    "characteristics": analysis_json["aggregated_characteristics"],
                    "subcharacteristics": analysis_json["aggregated_scs"],
                },
            }, requests.codes.ok

        data_for_analysis = {
            "pre_config": pre_config.to_json(),
            "components": components.to_json(),
        }

        resultado = requests.post(CORE_URL + "/analysis", json=data_for_analysis)

        resultado_j = resultado.json()

        AnalysisComponents(
            pre_config_id=data["pre_config_id"],
            sqc=resultado_j["sqc"],
            aggregated_scs=resultado_j["subcharacteristics"],
            aggregated_characteristics=resultado_j["characteristics"],
        ).save()

        data_for_return = {
            "pre_config": pre_config.to_json(),
            "components": components.to_json(),
            "analysis": resultado.json(),
        }

        return data_for_return, requests.codes.created
