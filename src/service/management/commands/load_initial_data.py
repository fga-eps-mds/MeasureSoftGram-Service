# Python Imports
import contextlib
import datetime as dt
import os

# 3rd Party Imports
import requests
from django.conf import settings

# Django Imports
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.utils import IntegrityError
from django.utils import timezone

import utils

# Local Imports
from utils import staticfiles
from service import models
from service.management.commands.utils import create_suported_characteristics
from organizations.models import Organization
from service.sub_views.collectors.sonarqube import import_sonar_metrics
from utils import (
    exceptions,
    get_random_datetime,
    get_random_path,
    get_random_qualifier,
    get_random_value,
)


class Command(BaseCommand):
    help = "Registra os dados iniciais no banco de dados"

    def create_suported_measures(self):
        """
        Função que popula banco de dados com todas as medidas que são
        suportadas atualmente e as métricas que cada medida é dependente
        """
        supported_measures = [
            {
                "key": "passed_tests",
                "metrics": [
                    {"key": "tests"},
                    {"key": "test_failures"},
                    {"key": "test_errors"},
                ],
            },
            {
                "key": "test_builds",
                "metrics": [
                    {"key": "test_execution_time"},
                ],
            },
            {
                "key": "test_coverage",
                "metrics": [
                    {"key": "coverage"},
                ],
            },
            {
                "key": "non_complex_file_density",
                "metrics": [
                    {"key": "functions"},
                    {"key": "complexity"},
                ],
            },
            {
                "key": "commented_file_density",
                "metrics": [
                    {"key": "comment_lines_density"},
                ],
            },
            {
                "key": "duplication_absense",
                "metrics": [
                    {"key": "duplicated_lines_density"},
                ],
            },
            {
                "key": "ci_feedback_time",
                "metrics": [
                    {"key": "number_of_build_pipelines_in_the_last_x_days"},
                    {"key": "runtime_sum_of_build_pipelines_in_the_last_x_days"},
                ],
            },
            {
                "key": "team_throughput",
                "metrics": [
                    {"key": "number_of_resolved_issues_in_the_last_x_days"},
                    {"key": "total_number_of_issues_in_the_last_x_days"},
                ],
            },
        ]
        for measure_data in supported_measures:
            measure_key = measure_data["key"]
            with contextlib.suppress(IntegrityError):
                measure_name = utils.namefy(measure_key)

                measure, _ = models.SupportedMeasure.objects.get_or_create(
                    key=measure_key,
                    name=measure_name,
                )

                metrics_keys = {
                    metric["key"]
                    for metric in measure_data["metrics"]
                }

                metrics = models.SupportedMetric.objects.filter(
                    key__in=metrics_keys,
                )

                if metrics.count() != len(metrics_keys):
                    raise exceptions.MissingSupportedMetricException()

                measure.metrics.set(metrics)

    def create_supported_metrics(self):
        self.create_sonarqube_supported_metrics()
        self.create_github_supported_metrics()

    def create_sonarqube_supported_metrics(self):
        sonar_endpoint = 'https://sonarcloud.io/api/metrics/search'

        try:
            request = requests.get(sonar_endpoint)

            if request.ok:
                data = request.json()
            else:
                data = staticfiles.SONARQUBE_AVAILABLE_METRICS
        except Exception:
            data = staticfiles.SONARQUBE_AVAILABLE_METRICS

        self.model_generator(models.SupportedMetric, data['metrics'])

        import_sonar_metrics(
            staticfiles.SONARQUBE_JSON,
            only_create_supported_metrics=True,
        )

    def create_github_supported_metrics(self):
        github_metrics = [
            models.SupportedMetric(
                key=metric['key'],
                name=metric['name'],
                metric_type=metric['metric_type'],
            ) for metric in settings.GITHUB_METRICS
        ]

        for metric in github_metrics:
            with contextlib.suppress(IntegrityError):
                metric.save()

    def model_generator(self, model, metrics):
        for metric in metrics:
            with contextlib.suppress(IntegrityError):
                model.objects.create(
                    key=metric['key'],
                    name=metric['name'],
                    description=metric.get('description', ''),
                    metric_type=metric['type'],
                )

    @staticmethod
    def create_fake_calculated_entity(qs, calculated_entity_factory, bulk_create_klass):
        if settings.CREATE_FAKE_DATA is False:
            return

        end_date = timezone.now()
        start_date = end_date - dt.timedelta(days=90)

        MIN_NUMBER_OF_CALCULATED_ENTITIES = 50
        MIN_NUMBER = MIN_NUMBER_OF_CALCULATED_ENTITIES

        fake_calculated_entities = []

        for entity in qs:
            if entity.qty <= MIN_NUMBER:
                created_at = get_random_datetime(start_date, end_date)
                for _ in range(MIN_NUMBER - entity.qty):
                    fake_calculated_entities.append(
                        calculated_entity_factory(entity, created_at),
                    )

        bulk_create_klass.objects.bulk_create(fake_calculated_entities)

    def create_fake_collected_metrics(self, repository):

        qs = models.SupportedMetric.objects.annotate(
            qty=Count('collected_metrics')
        )

        def calculated_entity_factory(entity, created_at):
            metric_type = entity.metric_type
            value = get_random_value(metric_type)

            return models.CollectedMetric(
                metric=entity,
                path=get_random_path(),
                qualifier=get_random_qualifier(),
                value=value,
                created_at=created_at,
                repository=repository,
            )

        self.create_fake_calculated_entity(
            qs,
            calculated_entity_factory,
            models.CollectedMetric,
        )

    def create_fake_calculated_measures(self, repository):

        qs = models.SupportedMeasure.objects.annotate(
            qty=Count('calculated_measures'),
        )

        def calculated_entity_factory(entity, created_at):
            return models.CalculatedMeasure(
                measure=entity,
                value=get_random_value('PERCENT'),
                created_at=created_at,
                repository=repository,
            )

        self.create_fake_calculated_entity(
            qs,
            calculated_entity_factory,
            models.CalculatedMeasure,
        )

    def create_suported_subcharacteristics(self):
        suported_subcharacteristics = [
            {
                "key": "modifiability",
                "name": "Modifiability",
                "measures": [
                    {"key": "duplication_absense"},
                    {"key": "commented_file_density"},
                    {"key": "non_complex_file_density"},
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
        ]

        for subcharacteristic in suported_subcharacteristics:
            with contextlib.suppress(IntegrityError):
                klass = models.SupportedSubCharacteristic

                sub_char, _ = klass.objects.get_or_create(
                    name=subcharacteristic['name'],
                    key=subcharacteristic['key'],
                )

                measures_keys = [
                    measure["key"]
                    for measure in subcharacteristic["measures"]
                ]

                measures = models.SupportedMeasure.objects.filter(
                    key__in=measures_keys,
                )

                sub_char.measures.set(measures)

    def create_suported_characteristics(self):
        suported_characteristics = [
            {
                "key": "reliability",
                "name": "Reliability",
                "subcharacteristics": [
                    {"key": "testing_status"},
                ]
            },
            {
                "key": "maintainability",
                "name": "Maintainability",
                "subcharacteristics": [
                    {"key": "modifiability"},
                ]
            },
        ]
        create_suported_characteristics(suported_characteristics)

    def create_fake_calculated_characteristics(self, repository):
        qs = models.SupportedCharacteristic.objects.annotate(
            qty=Count('calculated_characteristics'),
        )

        def calculated_entity_factory(entity, created_at):
            return models.CalculatedCharacteristic(
                characteristic=entity,
                value=get_random_value('PERCENT'),
                created_at=created_at,
                repository=repository,
            )

        self.create_fake_calculated_entity(
            qs,
            calculated_entity_factory,
            models.CalculatedCharacteristic,
        )

    def create_fake_calculated_subcharacteristics(self, repository):
        qs = models.SupportedSubCharacteristic.objects.annotate(
            qty=Count('calculated_subcharacteristics'),
        )

        def calculated_entity_factory(entity, created_at):
            return models.CalculatedSubCharacteristic(
                subcharacteristic=entity,
                value=get_random_value('PERCENT'),
                created_at=created_at,
                repository=repository,
            )

        self.create_fake_calculated_entity(
            qs,
            calculated_entity_factory,
            models.CalculatedSubCharacteristic,
        )

    def create_default_pre_config(self, repository):
        models.PreConfig.objects.get_or_create(
            name='Default pre-config',
            data=staticfiles.DEFAULT_PRE_CONFIG,
            repository=repository,
        )

    def create_fake_sqc_data(self, repository):
        if settings.CREATE_FAKE_DATA is False:
            return

        qs = models.SQC.objects.all()

        MIN_NUMBER = 50

        if qs.count() >= MIN_NUMBER:
            return

        models.SQC.objects.bulk_create([
            models.SQC(
                value=get_random_value('PERCENT'),
                repository=repository,
            )
            for _ in range(MIN_NUMBER - qs.count())
        ])

    def create_fake_organizations(self):
        if settings.CREATE_FAKE_DATA is False:
            return

        organizations = [
            Organization(
                name='fga-eps-mds',
                description=((
                    "Organização que agrupa os "
                    "projetos de EPS e MDS da FGA."
                )),
            ),
            Organization(
                name='UnBArqDsw2021',
                description=((
                    "Organização que agrupa os "
                    "projetos de Arquitetura e Desenvolvimento de "
                    "Software do semestre 2021.01"
                )),
            ),
            Organization(
                name='IHC-FGA-2020',
                description=((
                    "Organização que agrupa os projetos da" "disciplina de Interação Humano Computador"
                )),
            ),
        ]

        for organization in organizations:
            with contextlib.suppress(IntegrityError):
                organization.save()

    def create_fake_products(self):
        if settings.CREATE_FAKE_DATA is False:
            return

        = models.Organization.objects.all()

        organizations = {
            organization.name: organization
            for organization in organizations
        }

        products = [
            models.Product(
                name='Animalesco',
                description=(
                    "Uma aplicação para realizar o controle e "
                    "acompanhamento para com a saúde dos pets. "
                    "Os usuários, após se registrarem, podem "
                    "realizar o cadastro dos seus pets e a partir "
                    "disso fazer o acompanhamento do bichinho de "
                    "maneira digital."
                ),
                organization=organizations['UnBArqDsw2021'],
            ),
            models.Product(
                name='BCE UnB',
                description=(
                    "Este projeto possui o objetivo de analisar o "
                    "site da BCE, se propondo a sugerir melhorias "
                    "nos serviços de empréstimo de livros, "
                    "com base nos conceitos aprendidos na "
                    "discplina de IHC."
                ),
                organization=organizations['IHC-FGA-2020'],
            ),
            models.Product(
                name='MeasureSoftGram',
                description=(
                    "Este projeto que visa a construção de um "
                    "sistema de análise quantitativa da qualidade "
                    "de um sistema de software."
                ),
                organization=organizations['fga-eps-mds'],
            ),
            models.Product(
                name='Acacia',
                description=(
                    "Este projeto que visa a construção de um "
                    "sistema de colaboração de colheita de "
                    "árvores frutíferas em ambiente urbano."
                ),
                organization=organizations['fga-eps-mds'],
            ),
        ]

        for product in products:
            with contextlib.suppress(IntegrityError):
                product.save()

    def create_fake_repositories(self):
        if settings.CREATE_FAKE_DATA is False:
            return

        products = models.Product.objects.all()

        products = {
            product.name: product
            for product in products
        }

        repositories = [
            models.Repository(
                name='2019.2-Acacia',
                description=(
                    "Repositório do backend do projeto Acacia."
                ),
                product=products['Acacia'],
            ),
            models.Repository(
                name='2019.2-Acacia-Frontend',
                description=(
                    "Repositório do frontend do projeto Acacia."
                ),
                product=products['Acacia'],
            ),
            models.Repository(
                name='2019.2-Acacia-Frontend',
                description=(
                    "Repositório do frontend do projeto Acacia."
                ),
                product=products['Acacia'],
            ),
            models.Repository(
                name='2020.1-BCE',
                description=(
                    "Repositório do projeto BCE UnB."
                ),
                product=products['BCE UnB'],
            ),
            models.Repository(
                name='2021.1_G01_Animalesco_BackEnd',
                description=(
                    "Repositório do backend do projeto Animalesco."
                ),
                product=products['Animalesco'],
            ),
            models.Repository(
                name='2021.1_G01_Animalesco_FrontEnd',
                description=(
                    "Repositório do frontend "
                    "do projeto Animalesco."
                ),
                product=products['Animalesco'],
            ),
            models.Repository(
                name='2022-1-MeasureSoftGram-Service',
                description=(
                    "Repositório do backend do projeto "
                    "MeasureSoftGram."
                ),
                product=products['MeasureSoftGram'],
            ),
            models.Repository(
                name='2022-1-MeasureSoftGram-Core',
                description=(
                    "Repositório da API do modelo matemático "
                    "do projeto MeasureSoftGram"
                ),
                product=products['MeasureSoftGram'],
            ),
            models.Repository(
                name='2022-1-MeasureSoftGram-Front',
                description=(
                    "Repositório do frontend da projeto "
                    "MeasureSoftGram"
                ),
                product=products['MeasureSoftGram'],
            ),
            models.Repository(
                name='2022-1-MeasureSoftGram-CLI',
                description=(
                    "Repositório do CLI da projeto "
                    "MeasureSoftGram"
                ),
                product=products['MeasureSoftGram'],
            ),
        ]

        for repository in repositories:
            with contextlib.suppress(IntegrityError):
                repository.save()

    def handle(self, *args, **options):
        User = get_user_model()
        with contextlib.suppress(IntegrityError):
            User.objects.create_superuser(
                username=os.getenv('SUPERADMIN_USERNAME', 'admin'),
                email=os.getenv('SUPERADMIN_EMAIL', '"admin@admin.com"'),
                password=os.getenv('SUPERADMIN_PASSWORD', 'admin'),
            )

        self.create_fake_organizations()
        self.create_fake_products()
        self.create_fake_repositories()

        self.create_supported_metrics()
        self.create_suported_measures()
        self.create_suported_subcharacteristics()
        self.create_suported_characteristics()

        repositories = models.Repository.objects.all()

        for repository in repositories:
            self.create_fake_collected_metrics(repository)
            self.create_fake_calculated_measures(repository)
            self.create_fake_calculated_subcharacteristics(repository)
            self.create_fake_calculated_characteristics(repository)
            self.create_default_pre_config(repository)
            self.create_fake_sqc_data(repository)
