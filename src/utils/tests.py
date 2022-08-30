from rest_framework.test import APITestCase
from django.core.management import call_command


from utils import chunkify


class TestCaseExpanded(APITestCase):
    """
    Classe que agrupa rotinas e métodos que vários tests cases usam
    """
    @classmethod
    def setUpTestData(cls) -> None:
        call_command("load_initial_data")

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
