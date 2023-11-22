# testes para releases

from datetime import date, timedelta
from urllib import request

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse

from goals.models import Goal
from organizations.management.commands.utils import (
    create_a_preconfig,
    create_suported_characteristics,
)
from organizations.models import Product, Repository
from releases.models import Release
from utils.tests import APITestCaseExpanded
from rest_framework import status
from rest_framework.test import APIClient


class ReleaseEndpointsTestCase(APITestCaseExpanded):
    def setUp(self):
        self.client = APIClient()
        self.user = self.get_or_create_test_user()
        self.client.force_authenticate(
            self.user, token=Token.objects.create(user=self.user)
        )

        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.goal = Goal.objects.create(
            created_at=date.today(),
            created_by_id=self.user.id,
            product=self.product,
            data={
                "reliability": 53,
                "maintainability": 53,
                "functional_suitability": 53,
            },
        )
    
    def test_create_new_release_without_description(self):
        data = {
            "release_name": "testezada",
            "start_at": "2023-11-24",
            "end_at": "2023-11-25",
            "goal": self.goal.id
        }

        response = self.client.post(
            path=f'/api/v1/organizations/{self.org.id}/products/{self.product.id}/create/release/',
            data=data,
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        
        response_json = response.json()
        self.assertEqual(response_json["release_name"], "testezada")
        self.assertEqual(response_json["description"], None)
        self.assertEqual(response_json["start_at"], f"{data['start_at']}T00:00:00-03:00")
        self.assertEqual(response_json["end_at"], f"{data['end_at']}T00:00:00-03:00")
        self.assertEqual(response_json["created_by"], self.user.id)
        self.assertEqual(response_json["product"], self.product.id)
        self.assertEqual(response_json["goal"], data['goal'])
        self.assertEqual(response_json["description"], None)

    def test_create_new_release_full(self):
        data = {
            "release_name": "testezada 2",
            "start_at": "2023-11-24",
            "end_at": "2023-11-25",
            "goal": self.goal.id,
            "description": "Apenas um testezinho"
        }

        response = self.client.post(
            path=f'/api/v1/organizations/{self.org.id}/products/{self.product.id}/create/release/',
            data=data,
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        
        response_json = response.json()
        self.assertEqual(response_json["description"], "Apenas um testezinho")

    def test_create_two_releases_with_conflicting_dates(self):
        release1 = {
            "release_name": "testezada 1",
            "start_at": "2023-11-24",
            "end_at": "2023-11-30",
            "goal": self.goal.id,
            "description": "Essa tem que dar certo"
        }

        release2 = {
            "release_name": "testezada 2",
            "start_at": "2023-11-29",
            "end_at": "2023-12-03",
            "goal": self.goal.id,
            "description": "Essa tem que dar errado"
        }

        response_release1 = self.client.post(
            path=f'/api/v1/organizations/{self.org.id}/products/{self.product.id}/create/release/',
            data=release1,
            format="json"
        )

        response_release2 = self.client.post(
            path=f'/api/v1/organizations/{self.org.id}/products/{self.product.id}/create/release/',
            data=release2,
            format="json"
        )

        self.assertEqual(response_release1.status_code, 201)
        self.assertEqual(response_release2.status_code, 400)

        self.assertEqual(
            response_release2.json()["message"], 
            "The start date must be greater than the start date of the previous release"
        )

    def test_create_two_releases_with_conflicting_names(self):
        release1 = {
            "release_name": "testezada do baum",
            "start_at": "2023-11-24",
            "end_at": "2023-11-30",
            "goal": self.goal.id,
            "description": "Essa tem que dar certo"
        }

        release2 = {
            "release_name": "testezada do baum",
            "start_at": "2023-12-01",
            "end_at": "2023-12-03",
            "goal": self.goal.id,
            "description": "Essa tem que dar errado"
        }

        response_release1 = self.client.post(
            path=f'/api/v1/organizations/{self.org.id}/products/{self.product.id}/create/release/',
            data=release1,
            format="json"
        )

        response_release2 = self.client.post(
            path=f'/api/v1/organizations/{self.org.id}/products/{self.product.id}/create/release/',
            data=release2,
            format="json"
        )

        self.assertEqual(response_release1.status_code, 201)
        self.assertEqual(response_release2.status_code, 400)

        self.assertEqual(
            response_release2.json()["message"], 
            "The release name must be unique"
        )

    def test_create_releases_without_name(self):
        data = {
            "start_at": "2023-11-24",
            "end_at": "2023-11-30",
            "goal": self.goal.id
        }

        response = self.client.post(
            path=f'/api/v1/organizations/{self.org.id}/products/{self.product.id}/create/release/',
            data=data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_create_releases_without_goal(self):
        data = {
            "release_name": "testezada do baum",
            "start_at": "2023-11-24",
            "end_at": "2023-11-30"
        }

        response = self.client.post(
            path=f'/api/v1/organizations/{self.org.id}/products/{self.product.id}/create/release/',
            data=data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_create_releases_without_dates(self):
        data = {
            "release_name": "testezada do baum",
            "goal": self.goal.id,
            "description": "Essa tem que dar errado"
        }

        response = self.client.post(
            path=f'/api/v1/organizations/{self.org.id}/products/{self.product.id}/create/release/',
            data=data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    