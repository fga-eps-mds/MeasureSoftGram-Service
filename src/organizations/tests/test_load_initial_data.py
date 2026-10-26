import os
from unittest.mock import Mock, patch

from django.core.management import call_command

from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase, override_settings

from characteristics.models import BalanceMatrix, CalculatedCharacteristic, SupportedCharacteristic
from measures.models import CalculatedMeasure
from organizations.management.commands.load_initial_data import BADGE_DEMO_REPOSITORIES, Command
from organizations.management.commands.utils import create_balance_matrix
from goals.models import Goal
from organizations.models import Organization, Product, Repository
from releases.models import Release
from tsqmi.models import TSQMI
from utils.tests import APITestCaseExpanded

from staticfiles import SUPPORTED_MEASURES

from metrics.models import SupportedMetric


class LoadInitialDataBadgeDemoTestCase(APITestCaseExpanded):
    def setUp(self):
        self.command = Command()

    def test_create_badge_demo_repositories_is_idempotent(self):
        repositories = self.command.create_badge_demo_repositories()

        self.assertEqual(set(repositories.keys()), {"A", "B", "C", "D", "E", "N/A"})
        self.assertTrue(Organization.objects.filter(name="Badge Demo Organization").exists())

        organization = Organization.objects.get(name="Badge Demo Organization")
        product = Product.objects.get(
            name="Badge Demo Product",
            organization=organization,
        )

        self.assertEqual(product.repositories.count(), len(BADGE_DEMO_REPOSITORIES))

        repositories_again = self.command.create_badge_demo_repositories()
        self.assertEqual(set(repositories_again.keys()), set(repositories.keys()))
        self.assertEqual(product.repositories.count(), len(BADGE_DEMO_REPOSITORIES))

    def test_create_badge_demo_values_populates_expected_counts(self):
        repositories = self.command.create_badge_demo_repositories()

        repository_a = repositories["A"]
        TSQMI.objects.create(value=0.01, repository=repository_a)
        CalculatedCharacteristic.objects.create(
            characteristic=SupportedCharacteristic.objects.first(),
            value=0.01,
            repository=repository_a,
        )

        self.command.create_badge_demo_values(repositories)

        expected_characteristic_count = SupportedCharacteristic.objects.count()
        expected_values = {item["grade"]: item["value"] for item in BADGE_DEMO_REPOSITORIES}

        for grade, repository in repositories.items():
            if grade == "N/A":
                self.assertFalse(repository.calculated_tsqmis.exists())
                self.assertFalse(repository.calculated_characteristics.exists())
                continue

            self.assertEqual(repository.calculated_tsqmis.count(), 1)
            self.assertEqual(
                repository.calculated_characteristics.count(),
                expected_characteristic_count,
            )
            self.assertEqual(
                repository.calculated_tsqmis.first().value,
                expected_values[grade],
            )
            self.assertEqual(
                set(repository.calculated_characteristics.values_list("value", flat=True)),
                {expected_values[grade]},
            )

    def test_handle_enters_badge_demo_branch(
        self,
    ):
        with (
            patch.object(Command, "create_supported_metrics"),
            patch.object(Command, "create_suported_measures"),
            patch.object(Command, "create_github_suported_measures"),
            patch.object(Command, "create_supported_subcharacteristics"),
            patch.object(Command, "create_supported_characteristics"),
            patch.object(Command, "create_balance_matrix"),
            patch.object(Command, "create_fake_organizations"),
            patch.object(Command, "create_fake_products"),
            patch.object(Command, "create_fake_repositories"),
            patch.object(Command, "create_fake_collected_metrics") as mock_create_fake_collected_metrics,
            patch.object(Command, "create_fake_calculated_measures"),
            patch.object(Command, "create_fake_calculated_subcharacteristics"),
            patch.object(Command, "create_fake_calculated_characteristics"),
            patch.object(Command, "create_fake_tsqmi_data") as mock_create_fake_tsqmi_data,
            patch.object(Command, "create_badge_demo_repositories") as mock_create_badge_demo_repositories,
            patch.object(Command, "create_badge_demo_values") as mock_create_badge_demo_values,
            patch.object(Command, "create_a_goal"),
            patch.object(Command, "demo_repositories") as mock_demo_repositories,
            patch("organizations.management.commands.load_initial_data.get_user_model") as mock_get_user_model,
        ):
            mock_create_badge_demo_repositories.return_value = {"A": Mock()}
            mock_demo_repositories.return_value = [Mock()]
            mock_user_model = Mock()
            mock_user_model.objects.create_superuser.side_effect = IntegrityError()
            mock_get_user_model.return_value = mock_user_model

            self.command.handle(fake_data=True)

            mock_create_badge_demo_repositories.assert_called_once()
            mock_create_badge_demo_values.assert_called_once()
            mock_create_fake_collected_metrics.assert_called()
            mock_create_fake_tsqmi_data.assert_called()

    def test_create_balance_matrix_is_idempotent(self):
        characteristics = SupportedCharacteristic.objects.all()

        create_balance_matrix(characteristics)
        count_after_first_run = BalanceMatrix.objects.count()

        create_balance_matrix(characteristics)
        self.assertEqual(BalanceMatrix.objects.count(), count_after_first_run)


class LoadInitialDataFakeDataTestCase(APITestCaseExpanded):
    def setUp(self):
        self.command = Command()
        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.repository = self.get_repository(self.product)

    def test_create_fake_tsqmi_data_creates_entries(self):
        self.command.fake_data = True
        self.command.create_fake_tsqmi_data(self.repository)
        self.assertEqual(self.repository.calculated_tsqmis.count(), 50)

    @override_settings(CREATE_FAKE_DATA=False)
    def test_create_fake_tsqmi_data_skips_when_disabled(self):
        self.command.fake_data = False
        self.command.create_fake_tsqmi_data(self.repository)
        self.assertEqual(self.repository.calculated_tsqmis.count(), 0)

    def test_create_fake_tsqmi_data_skips_when_already_populated(self):
        for _ in range(50):
            TSQMI.objects.create(value=0.5, repository=self.repository)
        self.command.fake_data = True
        self.command.create_fake_tsqmi_data(self.repository)
        self.assertEqual(self.repository.calculated_tsqmis.count(), 50)

    def test_create_fake_calculated_measures_creates_entries(self):
        self.command.fake_data = True
        self.command.create_fake_calculated_measures(self.repository)

        calculated_keys = set(
            CalculatedMeasure.objects.filter(
                repository=self.repository,
            ).values_list("measure__key", flat=True)
        )

        expected_keys = {
            "passed_tests",
            "test_builds",
            "test_coverage",
            "non_complex_file_density",
            "commented_file_density",
            "duplication_absense",
            "team_throughput",
            "ci_feedback_time",
            "technical_debt_ratio",
        }

        self.assertEqual(calculated_keys, expected_keys)

    @override_settings(CREATE_FAKE_DATA=False)
    def test_create_fake_calculated_measures_skips_when_disabled(self):
        self.command.fake_data = False
        self.command.create_fake_calculated_measures(self.repository)
        self.assertFalse(CalculatedMeasure.objects.filter(repository=self.repository).exists())


class CoreMetricsRegistrationTestCase(TestCase):
    def test_registers_all_metrics_required_by_core(self):
        command = Command()
        command.create_supported_metrics()

        required_keys = {
            metric_key
            for measure in SUPPORTED_MEASURES
            for definition in measure.values()
            for metric_key in definition["metrics"]
        }
        registered_keys = set(
            SupportedMetric.objects.values_list("key", flat=True)
        )

        missing_keys = required_keys - registered_keys
        self.assertFalse(
            missing_keys,
            f"Métricas exigidas pelo Core sem cadastro: {sorted(missing_keys)}",
        )

    def test_runtime_metrics_registration_is_idempotent(self):
        command = Command()
        command.create_runtime_supported_metrics()
        command.create_runtime_supported_metrics()

        expected_keys = {
            "endpoint_calls",
            "mean_response_time",
            "cpu_usage",
            "memory_usage",
        }
        registered_keys = set(
            SupportedMetric.objects.values_list("key", flat=True)
        )

        self.assertEqual(registered_keys, expected_keys)
        self.assertEqual(SupportedMetric.objects.count(), 4)


@override_settings(CREATE_FAKE_DATA=False)
class LoadInitialDataProtegeDadosReaisTestCase(TransactionTestCase):
    """
    Regressão do BUG05.04 (#151): o load_initial_data roda a cada subida do
    container e não pode criar nem alterar nada em organizações, produtos e
    repositórios de usuários reais, com ou sem dados de demonstração.

    TransactionTestCase (sem transação envolvendo o teste) reproduz o
    autocommit do start_service.sh: o comando trata IntegrityError de
    entidades já cadastradas, o que quebraria a transação de um TestCase.
    """

    DEMO_ORG_NAMES = ("fga-eps-mds", "UnBArqDsw2021", "IHC-FGA-2020", "Badge Demo Organization")
    SEED_USERNAME = os.getenv("SEED_GITHUB_USERNAME", "msgramteste")

    def setUp(self):
        # Como no sistema real: a metodologia já existe quando o usuário cria
        # o produto (Product.save valida a pré-configuração contra ela).
        command = Command()
        command.create_supported_metrics()
        command.create_suported_measures()
        command.create_github_suported_measures()
        command.create_supported_subcharacteristics()
        command.create_supported_characteristics()

        self.user = get_user_model().objects.create_user(username="usuaria-real", password="senha-de-teste")
        self.org = Organization.objects.create(name="Org Real", admin=self.user)
        self.org.members.add(self.user)
        self.product = Product.objects.create(name="Produto Real", organization=self.org)
        self.repository = Repository.objects.create(name="repo-real", product=self.product)

    def assert_dados_reais_intactos(self):
        self.assertFalse(self.product.goals.exists())
        self.assertFalse(Release.objects.filter(product=self.product).exists())
        self.assertFalse(self.repository.collected_metrics.exists())
        self.assertFalse(self.repository.calculated_measures.exists())
        self.assertFalse(self.repository.calculated_subcharacteristics.exists())
        self.assertFalse(self.repository.calculated_characteristics.exists())
        self.assertFalse(self.repository.calculated_tsqmis.exists())
        self.assertFalse(self.org.members.filter(username=self.SEED_USERNAME).exists())

    def test_sem_flag_carrega_somente_a_metodologia(self):
        call_command("load_initial_data")

        self.assertTrue(SupportedMetric.objects.exists())
        self.assertTrue(SupportedCharacteristic.objects.exists())
        self.assertTrue(BalanceMatrix.objects.exists())
        self.assertFalse(Organization.objects.filter(name__in=self.DEMO_ORG_NAMES).exists())
        self.assert_dados_reais_intactos()

    def test_com_flag_nao_toca_em_dados_reais(self):
        call_command("load_initial_data", fake_data=True)

        self.assert_dados_reais_intactos()

        demo_repository = Repository.objects.get(name="2022-1-MeasureSoftGram-Service")
        self.assertTrue(demo_repository.calculated_tsqmis.exists())
        self.assertTrue(Release.objects.filter(product=demo_repository.product).exists())

    def test_com_flag_nao_usa_org_importada_do_github_com_nome_de_demo(self):
        org_importada = Organization.objects.create(name="fga-eps-mds", github_org_id=123, admin=self.user)
        org_importada.members.add(self.user)

        call_command("load_initial_data", fake_data=True)

        org_importada.refresh_from_db()
        self.assertEqual(org_importada.admin, self.user)
        self.assertFalse(org_importada.members.filter(username=self.SEED_USERNAME).exists())
        self.assertFalse(org_importada.products.exists())
        self.assertTrue(Organization.objects.filter(name="fga-eps-mds", github_org_id__isnull=True).exists())

    def test_rodar_duas_vezes_nao_duplica_dados_de_demonstracao(self):
        def contagem():
            return (
                Organization.objects.count(),
                Product.objects.count(),
                Repository.objects.count(),
                Goal.objects.count(),
                Release.objects.count(),
            )

        call_command("load_initial_data", fake_data=True)
        primeira = contagem()
        call_command("load_initial_data", fake_data=True)

        self.assertEqual(contagem(), primeira)
