from flask import Flask, request, jsonify
from flask_restful import Resource
from src.model.pre_config import PreConfig


class SelectedPreConfig(Resource):
    def post(self):
        data = request.get_json(force=True)

        pre_config = PreConfig(pre_config_name="teste")

        pre_config.caracteristcs = data

        pre_config.save()

        return pre_config.to_json(), 201
