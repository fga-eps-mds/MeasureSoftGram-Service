import sys
import threading

from django.test import TestCase

from characteristics.models import SupportedCharacteristic
from measures.models import SupportedMeasure
from subcharacteristics.models import SupportedSubCharacteristic

MODELS = (SupportedCharacteristic, SupportedSubCharacteristic, SupportedMeasure)


class SupportedEntityManagersTestCase(TestCase):
    """Os managers das entidades suportadas não guardam estado entre chamadas."""

    def test_each_thread_gets_a_queryset_of_its_own_model(self):
        # o antigo CacheManager guardava a última chamada num atributo de classe compartilhado por todas as threads:
        # com o servidor em threads, uma requisição de características recebia o queryset de medidas de outra
        wrong = []

        def query(model):
            for _ in range(3000):
                queryset = model.objects.filter(key__in=["x"])
                if queryset.model is not model:
                    wrong.append((model.__name__, queryset.model.__name__))
                    return

        threads = [threading.Thread(target=query, args=(model,)) for model in MODELS for _ in range(3)]
        # troca de thread a cada microssegundo, para as chamadas se intercalarem como em requisições simultâneas
        switch_interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        try:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        finally:
            sys.setswitchinterval(switch_interval)

        self.assertEqual(wrong, [])

    def test_filters_by_the_exact_key(self):
        # o CacheManager comparava strings como conjuntos de letras: "abc_teste" e "cba_teste" eram a mesma busca
        SupportedCharacteristic.objects.create(key="abc_teste", name="ABC")
        SupportedCharacteristic.objects.create(key="cba_teste", name="CBA")

        self.assertEqual(SupportedCharacteristic.objects.filter(key="abc_teste").get().name, "ABC")
        self.assertEqual(SupportedCharacteristic.objects.filter(key="cba_teste").get().name, "CBA")
