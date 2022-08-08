
import requests
from django.conf import settings
from requests.adapters import HTTPAdapter, Retry


class CoreClient:
    def __init__(self):
        self.host = settings.CORE_URL

    @staticmethod
    def configure_session(session):
        errors = [500, 502, 503, 504]
        retries = Retry(total=5, backoff_factor=5, status_forcelist=errors)
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))

    def calculate_measure(self, params):
        with requests.Session() as session:
            self.configure_session(session)
            url = f'{self.host}/calculate-measures/'
            return session.post(url, json=params)

    def calculate_subcharacteristic(self, params):
        with requests.Session() as session:
            self.configure_session(session)
            url = f'{self.host}/calculate-subcharacteristics/'
            return session.post(url, json=params)
