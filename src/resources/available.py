from flask_restful import Resource
from flask import jsonify
from src.util.constants import *
import requests


class AvailablePreConfigs(Resource):
    def get(self):
        return requests.get(
            CORE_URL + "/available-pre-configs",
            headers={"Accept": "application/json"},
        ).json()
