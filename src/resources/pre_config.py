from flask import Flask, request, jsonify
from flask_restful import Resource
from src.model.pre_config import PreConfig


class PreConfigs(Resource):
    def post(self):
        data = request.get_json(force=True)

        pre_config = PreConfig(
            name=data["name"], characteristics=data["characteristics"]
        ).save()

        return pre_config.to_json(), 201
