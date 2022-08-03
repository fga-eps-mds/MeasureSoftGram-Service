from django.test import TestCase

from utils import chunkify


class UtilsModuleTestCase(TestCase):
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
