
import requests
from django.conf import settings
from requests.adapters import HTTPAdapter, Retry
from rest_framework import status


class CoreClient:
    HOST = settings.CORE_URL

    @staticmethod
    def configure_session(session):
        errors = [500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511]
        retries = Retry(total=5, backoff_factor=5, status_forcelist=errors)
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))

    @staticmethod
    def make_post_request(url, params):
        with requests.Session() as session:
            CoreClient.configure_session(session)
            return session.post(url, json=params)

    @staticmethod
    def calculate_measure(params):
        url = f'{CoreClient.HOST}/calculate-measures/'
        return CoreClient.make_post_request(url, params)

    @staticmethod
    def calculate_subcharacteristic(params):
        url = f'{CoreClient.HOST}/calculate-subcharacteristics/'
        return CoreClient.make_post_request(url, params)

    @staticmethod
    def calculate_characteristic(params):
        url = f'{CoreClient.HOST}/calculate-characteristics/'
        return CoreClient.make_post_request(url, params)
