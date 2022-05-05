from flask_restful import Resource
from flask import request
from src.model.pre_config import PreConfig
from src.model.analysis import AnalysisComponents
from src.model.metrics_component_tree import MetricsComponentTree
import requests
from src.util.constants import CORE_URL
import mongoengine as me
from src.resources.utils import simple_error_response


class Analysis(Resource):
    def post(self):
        data = request.get_json(force=True)

        pre_configuration_id = data["pre_config_id"]

        try:
            pre_config = PreConfig.objects.with_id(pre_configuration_id)

            if pre_config is None:
                return simple_error_response(
                    f"There is no pre configurations with ID {pre_configuration_id}",
                    requests.codes.not_found,
                )
        except me.errors.ValidationError:
            return simple_error_response(
                f"{pre_configuration_id} is not a valid ID",
                requests.codes.not_found,
            )

        components = MetricsComponentTree.objects(
            pre_config_id=data["pre_config_id"]
        ).first()

        if components is None:
            return simple_error_response(
                f"There is no metrics file associated with this pre config {pre_configuration_id}",
                requests.codes.not_found,
            )

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
                    "weighted_measures": analysis_json["weighted_measures"],
                    "weighted_subcharacteristics": analysis_json["weighted_scs"],
                    "weighted_characteristics": analysis_json["weighted_c"],
                },
            }, requests.codes.ok

        data_for_analysis = {
            "pre_config": pre_config.to_json(),
            "components": components.to_json(),
        }

        resultado = requests.post(CORE_URL + "/analysis", json=data_for_analysis)

        if not 200 <= resultado.status_code <= 299:
            return resultado.json(), resultado.status_code

        analysis_json = resultado.json()

        AnalysisComponents(
            pre_config_id=data["pre_config_id"],
            sqc=analysis_json["sqc"],
            aggregated_scs=analysis_json["subcharacteristics"],
            aggregated_characteristics=analysis_json["characteristics"],
            weighted_measures=analysis_json["weighted_measures"],
            weighted_scs=analysis_json["weighted_subcharacteristics"],
            weighted_c=analysis_json["weighted_characteristics"],
        ).save()

        data_to_return = {
            "pre_config": pre_config.to_json(),
            "components": components.to_json(),
            "analysis": resultado.json(),
        }

        return data_to_return, requests.codes.created
