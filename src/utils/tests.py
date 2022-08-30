from rest_framework.test import APITestCase

from organizations.management.commands.load_initial_data import (
     Command as LoadInitialDataCommand
)

from organizations.models import Organization

from utils import chunkify


class APITestCaseExpanded(APITestCase):
    """
    Classe que agrupa rotinas e métodos que vários tests cases usam
    """
    @classmethod
    def setUpTestData(cls) -> None:
        command = LoadInitialDataCommand()
        command.create_supported_metrics()
        command.create_suported_measures()
        command.create_suported_subcharacteristics()
        command.create_suported_characteristics()

        # from django.core.management import call_command
        # call_command("load_initial_data")

    def get_organization(
        self,
        name="Test Organization",
        description="Test Organization Description",
    ):
        return Organization.objects.create(
            name=name,
            description=description,
        )

    def create_organization_product(
        self,
        org: Organization,
        name="Test Product",
        description="Test Product Description",

    ):
        return org.products.create(name=name, description=description)

    def create_product_repository(
        self,
        product,
        name="Test Repository",
        description="Test Repository Description",
    ):
        return product.repositories.create(
            name=name,
            description=description,
        )

    def validate_key(self, key):
        """
        Função auxiliar para validar se a key das
        entidades seguem o padrão de nomeação definido.
        """
        for c in key:
            self.assertTrue(
                c.islower() or c.isalnum() or c == '_',
                msg=(
                    "All characters in key must be lowercase and "
                    f"alphanumeric. The key is {key} and the "
                    f"failed char is {c}"
                ),
            )


class UtilsModuleTestCase(APITestCase):
    def test_chunkify(self):
        l_100 = list(range(100))
        self.assertEqual(
            chunkify(l_100, 10),
            [
                tuple(range(10)), tuple(range(10, 20)), tuple(range(20, 30)),
                tuple(range(30, 40)), tuple(range(40, 50)), tuple(range(50, 60)),
                tuple(range(60, 70)), tuple(range(70, 80)), tuple(range(80, 90)),
                tuple(range(90, 100)),
            ],
        )
