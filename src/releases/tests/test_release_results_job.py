import copy
from datetime import timedelta
from unittest import mock

from django.utils import timezone
from resources import calculate_characteristics

from characteristics.models import CalculatedCharacteristic
from goals.models import Goal
from release_configuration.models import ReleaseConfiguration
from releases.jobs import get_releases_and_create_results
from releases.models import Release
from subcharacteristics.models import CalculatedSubCharacteristic, SupportedSubCharacteristic
from utils.staticfiles import DEFAULT_PRE_CONFIG
from utils.tests import APITestCaseExpanded

CORE_RESULT = {
    "characteristics": [
        {"key": "reliability", "value": 0.7},
        {"key": "maintainability", "value": 0.4},
    ]
}

# último valor de cada subcaracterística da configuração padrão, que tem três características
SUBCHARACTERISTIC_VALUES = {
    "testing_status": 0.9,
    "maturity": 0.5,
    "modifiability": 0.6,
    "functional_completeness": 0.3,
}


@mock.patch("releases.jobs.calculate_characteristics", return_value=CORE_RESULT)
class GetReleasesAndCreateResultsTestCase(APITestCaseExpanded):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.org = self.get_organization()
        self.product = self.get_product(self.org)
        self.repository = self.get_repository(self.product)
        self.goal = Goal.objects.create(
            created_by=self.user,
            product=self.product,
            data={"reliability": 50, "maintainability": 50},
        )

    def create_release(self, end_at, repositories=None):
        release = Release.objects.create(
            release_name="Release teste",
            start_at=end_at - timedelta(days=7),
            end_at=end_at,
            created_by=self.user,
            product=self.product,
            goal=self.goal,
        )
        if repositories:
            release.repositories.set(repositories)
        return release

    def create_subcharacteristic_values(self, values):
        for key, value in values.items():
            CalculatedSubCharacteristic.objects.create(
                subcharacteristic=SupportedSubCharacteristic.objects.get(key=key),
                repository=self.repository,
                value=value,
            )

    def sent_subcharacteristic_weights(self, core):
        """Pesos das subcaracterísticas enviadas ao Core, por característica."""
        return {
            characteristic["key"]: {sub["key"]: sub["weight"] for sub in characteristic["subcharacteristics"]}
            for characteristic in core.call_args.args[0]["characteristics"]
        }

    def test_does_nothing_when_no_release_ends_today(self, core):
        self.create_release(end_at=timezone.now() - timedelta(days=3))

        get_releases_and_create_results()

        core.assert_not_called()
        self.assertFalse(CalculatedCharacteristic.objects.exists())

    def test_creates_results_for_release_repositories(self, core):
        release = self.create_release(end_at=timezone.now(), repositories=[self.repository])

        with self.assertLogs("releases.jobs", level="INFO") as logs:
            get_releases_and_create_results()

        results = CalculatedCharacteristic.objects.filter(release=release, repository=self.repository)
        self.assertEqual(
            {(r.characteristic.key, r.value) for r in results},
            {("reliability", 0.7), ("maintainability", 0.4)},
        )
        self.assertIn("Características calculadas criadas", logs.output[0])

    def test_uses_product_repositories_when_release_has_none(self, core):
        other_repository = self.get_repository(self.product, name="Outro Repositorio")
        release = self.create_release(end_at=timezone.now())

        get_releases_and_create_results()

        self.assertEqual(
            set(CalculatedCharacteristic.objects.filter(release=release).values_list("repository_id", flat=True)),
            {self.repository.id, other_repository.id},
        )

    def test_logs_exception_when_bulk_create_fails(self, core):
        self.create_release(end_at=timezone.now(), repositories=[self.repository])

        with (
            mock.patch.object(CalculatedCharacteristic.objects, "bulk_create", side_effect=Exception("falhou")),
            self.assertLogs("releases.jobs", level="ERROR") as logs,
        ):
            get_releases_and_create_results()

        self.assertIn("Erro ao criar as características calculadas", logs.output[0])
        self.assertFalse(CalculatedCharacteristic.objects.exists())

    def test_calls_core_once_per_release_with_latest_subcharacteristic_values(self, core):
        other_repository = self.get_repository(self.product, name="Outro Repositorio")
        modifiability = SupportedSubCharacteristic.objects.get(key="modifiability")
        for value, days_ago in ((0.2, 3), (0.9, 1)):
            CalculatedSubCharacteristic.objects.create(
                subcharacteristic=modifiability,
                repository=self.repository,
                value=value,
                created_at=timezone.now() - timedelta(days=days_ago),
            )
        self.create_release(end_at=timezone.now(), repositories=[self.repository, other_repository])

        get_releases_and_create_results()

        core.assert_called_once()
        params = core.call_args.args[0]
        subcharacteristics = {
            sub["key"]: sub["value"] for char in params["characteristics"] for sub in char["subcharacteristics"]
        }
        self.assertEqual(subcharacteristics["modifiability"], 0.9)
        self.assertEqual(CalculatedCharacteristic.objects.count(), 4)

    def test_calculates_every_characteristic_of_the_release_configuration(self, core):
        core.side_effect = calculate_characteristics
        self.create_subcharacteristic_values(SUBCHARACTERISTIC_VALUES)
        release = self.create_release(end_at=timezone.now(), repositories=[self.repository])

        get_releases_and_create_results()

        results = CalculatedCharacteristic.objects.filter(release=release, repository=self.repository)
        self.assertEqual(
            {r.characteristic.key for r in results},
            {"reliability", "maintainability", "functional_suitability"},
        )

    def test_uses_the_configuration_of_the_release_instead_of_the_current_one(self, core):
        end_at = timezone.now()
        release_data = copy.deepcopy(DEFAULT_PRE_CONFIG)
        testing_status, maturity = release_data["characteristics"][0]["subcharacteristics"]
        testing_status["weight"], maturity["weight"] = 80, 20
        current_data = copy.deepcopy(DEFAULT_PRE_CONFIG)
        current_data["characteristics"] = current_data["characteristics"][:2]
        current_data["characteristics"][0]["weight"] = current_data["characteristics"][1]["weight"] = 50
        self.product.release_configuration.all().delete()
        ReleaseConfiguration.objects.create(
            product=self.product, name="Da release", data=release_data, created_at=end_at - timedelta(days=30)
        )
        # criada depois do fim da release: é a atual do produto, mas não vale para a release
        ReleaseConfiguration.objects.create(
            product=self.product, name="Atual", data=current_data, created_at=end_at + timedelta(hours=1)
        )
        self.create_subcharacteristic_values(SUBCHARACTERISTIC_VALUES)
        self.create_release(end_at=end_at, repositories=[self.repository])

        get_releases_and_create_results()

        self.assertEqual(
            self.sent_subcharacteristic_weights(core),
            {
                "reliability": {"testing_status": 80, "maturity": 20},
                "maintainability": {"modifiability": 100},
                "functional_suitability": {"functional_completeness": 100},
            },
        )

    def test_characteristic_without_calculated_subcharacteristics_does_not_stop_the_others(self, core):
        core.side_effect = calculate_characteristics
        # sem maturity e sem functional_completeness, a única subcaracterística de functional_suitability
        self.create_subcharacteristic_values({"testing_status": 0.9, "modifiability": 0.6})
        release = self.create_release(end_at=timezone.now(), repositories=[self.repository])

        get_releases_and_create_results()

        self.assertEqual(
            self.sent_subcharacteristic_weights(core),
            {"reliability": {"testing_status": 50}, "maintainability": {"modifiability": 100}},
        )
        self.assertEqual(
            {r.characteristic.key for r in CalculatedCharacteristic.objects.filter(release=release)},
            {"reliability", "maintainability"},
        )
