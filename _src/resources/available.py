from flask_restful import Resource
from _src.util.constants import CORE_URL
import requests


class AvailablePreConfigs(Resource):
    def get(self):
        return requests.get(
            CORE_URL + "/available-pre-configs",
            headers={"Accept": "application/json"},
        ).json()
