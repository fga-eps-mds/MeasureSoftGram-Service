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
    
