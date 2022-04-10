from flask import Flask, request, jsonify
from flask_restful import Resource
from src.model.pre_config import PreConfig
import requests
import mongoengine as me


class PreConfigs(Resource):
    def post(self):
        data = request.get_json(force=True)

        try:
            pre_config = PreConfig(data).save()
        except me.errors.ValidationError:
            return {
                "error": "The pre config name is already in use"
            }, requests.codes.unprocessable_entity

        return pre_config.to_json(), requests.codes.created
