# Python Imports
import contextlib
import datetime as dt
import logging
import os

# 3rd Party Imports
from django.conf import settings

# Django Imports
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone
from staticfiles import SUPPORTED_MEASURES

import utils
from math_model.models import QualityAnalysis
from utils.demo_payload import demo_payload, persist_demo_analysis

from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from goals.serializers import GoalSerializer
from measures.models import SupportedMeasure
from metrics.models import SupportedMetric
from organizations.models import Organization, Product, Repository
from release_configuration.models import ReleaseConfiguration
from releases.models import Release
from subcharacteristics.models import SupportedSubCharacteristic
from tsqmi.models import TSQMI
from utils.runtime_metrics import (
    RUNTIME_AVAILABLE_METRICS,
)

# Local Imports
from utils import exceptions, staticfiles

from .utils import create_balance_matrix, create_supported_characteristics, get_random_goal_data

logger = logging.getLogger(__name__)


# Organizações criadas pelo seed de demonstração. O seed só pode ler e escrever
# dentro delas (ver Command.demo_organizations) — BUG05.04 (#151).
BADGE_DEMO_ORGANIZATION_NAME = "Badge Demo Organization"
DEMO_ORGANIZATION_NAMES = (
    "fga-eps-mds",
    "UnBArqDsw2021",
    "IHC-FGA-2020",
    BADGE_DEMO_ORGANIZATION_NAME,
)

BADGE_DEMO_REPOSITORIES = [
    {
        "name": "Badge Demo A",
        "grade": "A",
        "value": 0.90,
        "description": "Repositório mockado para teste visual da badge A.",
    },
    {
        "name": "Badge Demo B",
        "grade": "B",
        "value": 0.70,
        "description": "Repositório mockado para teste visual da badge B.",
    },
    {
        "name": "Badge Demo C",
        "grade": "C",
        "value": 0.50,
        "description": "Repositório mockado para teste visual da badge C.",
    },
    {
        "name": "Badge Demo D",
        "grade": "D",
        "value": 0.30,
        "description": "Repositório mockado para teste visual da badge D.",
    },
    {
        "name": "Badge Demo E",
        "grade": "E",
        "value": 0.10,
        "description": "Repositório mockado para teste visual da badge E.",
    },
    {
        "name": "Badge Demo N-A",
        "grade": "N/A",
        "value": None,
        "description": "Repositório mockado sem valor atual para testar badge N/A.",
    },
]


class Command(BaseCommand):
    help = "Registra os dados iniciais no banco de dados"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-demo-analyses",
            action="store_true",
            help="Recria somente análises dos repositórios locais de demonstração; preserva organizações importadas.",
        )
        # Create fake data
        parser.add_argument(
            "--fake-data",
            action="store_true",
            help="Cria dados de demonstração (somente nas organizações de demonstração)",
        )

    def create_suported_measures(self):
        """
        Função que popula banco de dados com todas as medidas que são
        suportadas atualmente e as métricas que cada medida é dependente
        """
        self._create_measures_with_metrics(SUPPORTED_MEASURES)

    def create_github_suported_measures(self):
        """
        Função que popula banco de dados com todas as medidas que são
        suportadas atualmente e as métricas que cada medida é dependente
        """
        self._create_measures_with_metrics(settings.GITHUB_SUPPORTED_MEASURES)

    def _create_measures_with_metrics(self, supported_measures):
        for measure_data in supported_measures:
            measure_key = next(iter(measure_data))
            with contextlib.suppress(IntegrityError), transaction.atomic():
                measure_name = utils.namefy(measure_key)

                # `key` é único e `name` não: buscar pelos dois falha em medida já cadastrada com outro nome.
                measure, _ = SupportedMeasure.objects.get_or_create(
                    key=measure_key,
                    defaults={"name": measure_name},
                )

                logger.info(f"Creating supported measure {measure_key}")

                metrics_keys = set(measure_data[measure_key]["metrics"])

                metrics = SupportedMetric.objects.filter(
                    key__in=metrics_keys,
                )

                if metrics.count() != len(metrics_keys):
                    raise exceptions.MissingSupportedMetricException()

                measure.metrics.set(metrics)
                logger.info(f"Metrics {','.join(metrics_keys)} " f"were associated to {measure_key}")

    def create_supported_metrics(self):
        self.create_sonarqube_supported_metrics()
        self.create_github_supported_metrics()
        self.create_runtime_supported_metrics()

    def create_runtime_supported_metrics(self):
        for metric in RUNTIME_AVAILABLE_METRICS:
            SupportedMetric.objects.get_or_create(
                key=metric["key"],
                defaults={
                    "name": metric["name"],
                    "metric_type": metric["metric_type"],
                },
            )

    def create_sonarqube_supported_metrics(self):
        data = staticfiles.SONARQUBE_AVAILABLE_METRICS

        sonar_metrics = [
            SupportedMetric(
                key=metric["key"],
                name=metric["name"],
                metric_type=metric["metric_type"],
            )
            for metric in data
        ]
        for metric in sonar_metrics:
            with contextlib.suppress(IntegrityError), transaction.atomic():
                metric.save()

    def create_github_supported_metrics(self):
        github_metrics = [
            SupportedMetric(
                key=metric["key"],
                name=metric["name"],
                metric_type=metric["metric_type"],
            )
            for metric in staticfiles.GITHUB_AVAILABLE_METRICS
        ]

        for metric in github_metrics:
            with contextlib.suppress(IntegrityError), transaction.atomic():
                metric.save()

    def model_generator(self, model, metrics):
        for metric in metrics:
            with contextlib.suppress(IntegrityError), transaction.atomic():
                model.objects.create(
                    key=metric["key"],
                    name=metric["name"],
                    description=metric.get("description", ""),
                    metric_type=metric["type"],
                )

    def create_supported_subcharacteristics(self):
        supported_subcharacteristics = [
            {
                "key": "modifiability",
                "name": "Modifiability",
                "measures": [
                    {"key": "duplication_absense"},
                    {"key": "commented_file_density"},
                    {"key": "non_complex_file_density"},
                    {"key": "technical_debt_ratio"},
                ],
            },
            {
                "key": "testing_status",
                "name": "Testing Status",
                "measures": [
                    {"key": "test_coverage"},
                    {"key": "test_builds"},
                    {"key": "passed_tests"},
                ],
            },
            {
                "key": "functional_completeness",
                "name": "Functional Completeness",
                "measures": [
                    {"key": "team_throughput"},
                ],
            },
            {
                "key": "maturity",
                "name": "Maturity",
                "measures": [
                    {"key": "ci_feedback_time"},
                ],
            },
        ]

        for subcharacteristic in supported_subcharacteristics:
            with contextlib.suppress(IntegrityError), transaction.atomic():
                klass = SupportedSubCharacteristic

                sub_char, _ = klass.objects.get_or_create(
                    name=subcharacteristic["name"],
                    key=subcharacteristic["key"],
                )

                measures_keys = [measure["key"] for measure in subcharacteristic["measures"]]

                measures = SupportedMeasure.objects.filter(
                    key__in=measures_keys,
                )

                if measures.count() != len(measures_keys):
                    raise exceptions.MissingSupportedMeasureException()

                sub_char.measures.set(measures)

    def create_supported_characteristics(self):
        supported_characteristics = [
            {
                "key": "reliability",
                "name": "Reliability",
                "subcharacteristics": [
                    {"key": "testing_status"},
                    {"key": "maturity"},
                ],
            },
            {
                "key": "maintainability",
                "name": "Maintainability",
                "subcharacteristics": [
                    {"key": "modifiability"},
                ],
            },
            {
                "key": "functional_suitability",
                "name": "Functional Suitability",
                "subcharacteristics": [
                    {"key": "functional_completeness"},
                ],
            },
        ]
        create_supported_characteristics(supported_characteristics)

    def create_balance_matrix(self):
        characteristics = SupportedCharacteristic.objects.all()
        create_balance_matrix(characteristics)

    def demo_organizations(self):
        """
        Organizações de demonstração: as criadas pelo seed. Uma organização
        importada do GitHub nunca é de demonstração, mesmo com o mesmo nome
        (ex.: a org real fga-eps-mds) — BUG05.04 (#151).
        """
        return Organization.objects.filter(
            name__in=DEMO_ORGANIZATION_NAMES,
            github_org_id__isnull=True,
        )

    def demo_products(self):
        return Product.objects.filter(organization__in=self.demo_organizations())

    def demo_repositories(self):
        return Repository.objects.filter(product__organization__in=self.demo_organizations())

    def create_default_pre_config(self, product):
        ReleaseConfiguration.objects.get_or_create(
            name="Default pre-config",
            data=staticfiles.DEFAULT_PRE_CONFIG,
            product=product,
        )

    def get_seed_user(self):
        """
        Retorna (criando se necessário) o usuário dono dos dados semente.

        Com o login via GitHub, os dados só ficam visíveis para o usuário que
        for membro da organização. Por isso os dados semente são vinculados à
        conta de teste do GitHub (identificada pelo username do GitHub, que é o
        valor que o allauth grava ao logar). Os valores podem ser sobrescritos
        via variáveis de ambiente.
        """
        user_model = get_user_model()
        username = os.getenv("SEED_GITHUB_USERNAME", "msgramteste")
        email = os.getenv("SEED_GITHUB_EMAIL", "msgram.teste@gmail.com")
        user, _ = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        return user

    def create_a_goal(self, product: Product):
        if product.goals.exists():
            return
        pre_config = product.release_configuration.first()
        data = get_random_goal_data(pre_config)
        serializer = GoalSerializer(data=data)

        class MockView:
            @staticmethod
            def get_product():
                return product

        serializer.context["view"] = MockView
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product, created_by=self.get_seed_user())

    def create_a_release(self, product: Product):
        """
        Cria releases de demonstração para um produto (uma concluída e uma em
        andamento), vinculadas à goal do produto. As janelas ficam dentro dos
        últimos ~90 dias, período coberto pelos dados fake, para que a
        comparação planejado x realizado tenha dados.
        """
        if Release.objects.filter(product=product).exists():
            return

        goal = product.goals.first()
        if goal is None:
            return

        seed_user = self.get_seed_user()
        now = timezone.now()

        releases = [
            {
                "release_name": f"{product.name} - Release 1",
                "start_at": now - dt.timedelta(days=90),
                "end_at": now - dt.timedelta(days=46),
                "description": ("Release inicial (concluída) gerada para demonstração."),
            },
            {
                "release_name": f"{product.name} - Release 2",
                "start_at": now - dt.timedelta(days=45),
                "end_at": now + dt.timedelta(days=15),
                "description": ("Release em andamento gerada para demonstração."),
            },
        ]

        for release_data in releases:
            Release.objects.create(
                release_name=release_data["release_name"],
                start_at=release_data["start_at"],
                end_at=release_data["end_at"],
                description=release_data["description"],
                created_by=seed_user,
                product=product,
                goal=goal,
            )

    def create_fake_organizations(self):
        organizations = [
            Organization(
                name="fga-eps-mds",
                description=("Organização que agrupa os " "projetos de EPS e MDS da FGA."),
            ),
            Organization(
                name="UnBArqDsw2021",
                description=(
                    "Organização que agrupa os "
                    "projetos de Arquitetura e Desenvolvimento de "
                    "Software do semestre 2021.01"
                ),
            ),
            Organization(
                name="IHC-FGA-2020",
                description=("Organização que agrupa os projetos da disciplina de " "Interação Humano Computador"),
            ),
        ]

        for organization in organizations:
            existing = self.demo_organizations().filter(name=organization.name).first()
            if existing:
                organization = existing
            else:
                organization.save()

            if organization.admin is None:
                organization.admin = self.get_seed_user()
                organization.save()
            organization.members.add(self.get_seed_user())

    def create_fake_products(self):
        organizations = self.demo_organizations()

        organizations = {organization.name: organization for organization in organizations}

        products = [
            Product(
                name="Animalesco",
                description=(
                    "Uma aplicação para realizar o controle e "
                    "acompanhamento para com a saúde dos pets. "
                    "Os usuários, após se registrarem, podem "
                    "realizar o cadastro dos seus pets e a partir "
                    "disso fazer o acompanhamento do bichinho de "
                    "maneira digital."
                ),
                organization=organizations["UnBArqDsw2021"],
            ),
            Product(
                name="BCE UnB",
                description=(
                    "Este projeto possui o objetivo de analisar o "
                    "site da BCE, se propondo a sugerir melhorias "
                    "nos serviços de empréstimo de livros, "
                    "com base nos conceitos aprendidos na "
                    "discplina de IHC."
                ),
                organization=organizations["IHC-FGA-2020"],
            ),
            Product(
                name="MeasureSoftGram",
                description=(
                    "Este projeto que visa a construção de um "
                    "sistema de análise quantitativa da qualidade "
                    "de um sistema de software."
                ),
                organization=organizations["fga-eps-mds"],
            ),
            Product(
                name="Acacia",
                description=(
                    "Este projeto que visa a construção de um "
                    "sistema de colaboração de colheita de "
                    "árvores frutíferas em ambiente urbano."
                ),
                organization=organizations["fga-eps-mds"],
            ),
        ]

        for product in products:
            if Product.objects.filter(
                name=product.name,
                organization=product.organization,
            ).exists():
                continue
            product.save()

    def create_fake_repositories(self):
        products = self.demo_products()

        products = {product.name: product for product in products}

        repositories = [
            Repository(
                name="2019.2-Acacia",
                description=("Repositório do backend do projeto Acacia."),
                product=products["Acacia"],
            ),
            Repository(
                name="2019.2-Acacia-Frontend",
                description=("Repositório do frontend do projeto Acacia."),
                product=products["Acacia"],
            ),
            Repository(
                name="2019.2-Acacia-Frontend",
                description=("Repositório do frontend do projeto Acacia."),
                product=products["Acacia"],
            ),
            Repository(
                name="2020.1-BCE",
                description=("Repositório do projeto BCE UnB."),
                product=products["BCE UnB"],
            ),
            Repository(
                name="2021.1_G01_Animalesco_BackEnd",
                description=("Repositório do backend do projeto Animalesco."),
                product=products["Animalesco"],
            ),
            Repository(
                name="2021.1_G01_Animalesco_FrontEnd",
                description="Repositório do frontend do projeto Animalesco.",
                product=products["Animalesco"],
            ),
            Repository(
                name="2022-1-MeasureSoftGram-Service",
                description="Repositório do backend do projeto MeasureSoftGram.",
                product=products["MeasureSoftGram"],
            ),
            Repository(
                name="2022-1-MeasureSoftGram-Core",
                description=("Repositório da API do modelo matemático " "do projeto MeasureSoftGram"),
                product=products["MeasureSoftGram"],
            ),
            Repository(
                name="2022-1-MeasureSoftGram-Front",
                description="Repositório do frontend da projeto MeasureSoftGram",
                product=products["MeasureSoftGram"],
            ),
            Repository(
                name="2022-1-MeasureSoftGram-CLI",
                description="Repositório do CLI da projeto MeasureSoftGram",
                product=products["MeasureSoftGram"],
            ),
        ]

        for repository in repositories:
            if Repository.objects.filter(
                name=repository.name,
                product=repository.product,
            ).exists():
                continue
            repository.save()

    def create_badge_demo_repositories(self):
        organization, _ = Organization.objects.update_or_create(
            name=BADGE_DEMO_ORGANIZATION_NAME,
            github_org_id=None,
            defaults={
                "description": ("Organização mockada para validar visualmente as badges " "A, B, C, D, E e N/A."),
            },
        )

        if organization.admin is None:
            organization.admin = self.get_seed_user()
            organization.save()
        organization.members.add(self.get_seed_user())

        product, _ = Product.objects.get_or_create(
            name="Badge Demo Product",
            organization=organization,
            defaults={
                "description": (
                    "Produto mockado com um repositório para cada tipo de " "badge suportada pelo sistema."
                ),
            },
        )

        repositories = {}
        for repo_data in BADGE_DEMO_REPOSITORIES:
            repository, _ = Repository.objects.update_or_create(
                name=repo_data["name"],
                product=product,
                defaults={
                    "description": repo_data["description"],
                    "platform": "github",
                    "imported": True,
                },
            )
            repositories[repo_data["grade"]] = repository

        return repositories

    def create_badge_demo_values(self, repositories):
        characteristics = list(SupportedCharacteristic.objects.all())
        created_at = timezone.now()

        for repo_data in BADGE_DEMO_REPOSITORIES:
            repository = repositories[repo_data["grade"]]

            repository.quality_analyses.all().delete()

            if repo_data["value"] is None:
                continue

            analysis = QualityAnalysis.objects.create(
                repository=repository,
                created_at=created_at,
                is_partial=True,
                missing_inputs=["badge_demo:characteristics_only"],
            )
            TSQMI.objects.create(
                analysis=analysis,
                value=repo_data["value"],
                repository=repository,
                created_at=created_at,
            )

            CalculatedCharacteristic.objects.bulk_create(
                [
                    CalculatedCharacteristic(
                        analysis=analysis,
                        characteristic=characteristic,
                        value=repo_data["value"],
                        created_at=created_at,
                        repository=repository,
                    )
                    for characteristic in characteristics
                ]
            )

    @transaction.atomic
    def create_fake_analyses(self, repository):
        """Executa o mesmo cálculo da Action; nunca gera camadas independentes."""
        if not (settings.CREATE_FAKE_DATA or getattr(self, "fake_data", False)):
            return
        if repository.quality_analyses.exists():
            return
        for day in range(89, -1, -3):
            at = timezone.now() - dt.timedelta(days=day)
            persist_demo_analysis(repository, at, demo_payload(day))

    def handle(self, *args, **kwargs):
        self.fake_data = kwargs.get("fake_data") or kwargs.get("reset_demo_analyses")

        user_model = get_user_model()
        with contextlib.suppress(IntegrityError), transaction.atomic():
            user_model.objects.create_superuser(
                username=os.getenv("SUPERADMIN_USERNAME", "admin"),
                email=os.getenv("SUPERADMIN_EMAIL", "admin@admin.com"),
                password=os.getenv("SUPERADMIN_PASSWORD", "admin"),
            )

        # Metodologia: roda a cada subida, é idempotente e não toca em dados
        # de usuários.
        self.create_supported_metrics()
        self.create_suported_measures()
        self.create_github_suported_measures()
        self.create_supported_subcharacteristics()
        self.create_supported_characteristics()
        self.create_balance_matrix()

        # Demonstração: só com CREATE_FAKE_DATA ou --fake-data, e só dentro
        # das organizações de demonstração — BUG05.04 (#151).
        if not (settings.CREATE_FAKE_DATA or self.fake_data):
            return

        self.create_fake_organizations()
        self.create_fake_products()
        self.create_fake_repositories()
        badge_demo_repositories = self.create_badge_demo_repositories()

        if kwargs.get("reset_demo_analyses"):
            QualityAnalysis.objects.filter(repository__in=self.demo_repositories()).delete()

        for product in self.demo_products():
            self.create_a_goal(product)
            self.create_a_release(product)

        for repository in self.demo_repositories():
            self.create_fake_analyses(repository)

        self.create_badge_demo_values(badge_demo_repositories)
