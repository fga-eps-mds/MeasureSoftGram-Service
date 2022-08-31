import os
import random


class IResponse:
    def __init__(
        self,
        _json: dict,
        _status_code: int = 200,
    ) -> None:
        self._json = _json
        self._status_code = _status_code

    @property
    def ok(self):
        return 200 <= self._status_code < 300

    @property
    def status_code(self):
        return self._status_code

    def json(self):
        return self._json


class Mocks:
    @staticmethod
    def calculate_measure(params):
        _status_code = int(os.getenv("RESPONSE_HTTP_STATUS_CODE", "200"))
        _json = {
            'measures': [
                {'key': measure['key'], 'value': random.random()}
                for measure in params['measures']
            ]
        }
        return IResponse(_json=_json, _status_code=_status_code)
