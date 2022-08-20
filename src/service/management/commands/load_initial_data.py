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
from service import models, staticfiles
from service.management.commands.utils import create_suported_characteristics
from service.sub_views.collectors.sonarqube import import_sonar_metrics
from utils import (
    exceptions,
    get_random_datetime,
    get_random_path,
    get_random_qualifier,
    get_random_value,
)

User = get_user_model()


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

        request = requests.get(sonar_endpoint)

        if request.ok:
            data = request.json()
        else:
            data = staticfiles.SONARQUBE_AVAILABLE_METRICS

        self.model_generator(models.SupportedMetric, data['metrics'])

        import_sonar_metrics(staticfiles.SONARQUBE_JSON)

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

    def create_fake_collected_metrics(self):

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
            )

        self.create_fake_calculated_entity(
            qs,
            calculated_entity_factory,
            models.CollectedMetric,
        )

    def create_fake_calculated_measures(self):

        qs = models.SupportedMeasure.objects.annotate(
            qty=Count('calculated_measures'),
        )

        def calculated_entity_factory(entity, created_at):
            return models.CalculatedMeasure(
                measure=entity,
                value=get_random_value('PERCENT'),
                created_at=created_at,
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

    def create_fake_calculated_characteristics(self):
        qs = models.SupportedCharacteristic.objects.annotate(
            qty=Count('calculated_characteristics'),
        )

        def calculated_entity_factory(entity, created_at):
            return models.CalculatedCharacteristic(
                characteristic=entity,
                value=get_random_value('PERCENT'),
                created_at=created_at,
            )

        self.create_fake_calculated_entity(
            qs,
            calculated_entity_factory,
            models.CalculatedCharacteristic,
        )

    def create_fake_calculated_subcharacteristics(self):
        qs = models.SupportedSubCharacteristic.objects.annotate(
            qty=Count('calculated_subcharacteristics'),
        )

        def calculated_entity_factory(entity, created_at):
            return models.CalculatedSubCharacteristic(
                subcharacteristic=entity,
                value=get_random_value('PERCENT'),
                created_at=created_at,
            )

        self.create_fake_calculated_entity(
            qs,
            calculated_entity_factory,
            models.CalculatedSubCharacteristic,
        )

    def create_default_pre_config(self):
        models.PreConfig.objects.get_or_create(
            name='Default pre-config',
            data=staticfiles.DEFAULT_PRE_CONFIG,
        )

    def create_fake_sqc_data(self):
        if settings.CREATE_FAKE_DATA is False:
            return

        qs = models.SQC.objects.all()

        MIN_NUMBER = 50

        if qs.count() >= MIN_NUMBER:
            return

        models.SQC.objects.bulk_create([
            models.SQC(
                value=get_random_value('PERCENT'),
            )
            for _ in range(MIN_NUMBER - qs.count())
        ])

    def handle(self, *args, **options):
        with contextlib.suppress(IntegrityError):
            User.objects.create_superuser(
                username=os.getenv('SUPERADMIN_USERNAME', 'admin'),
                email=os.getenv('SUPERADMIN_EMAIL', '"admin@admin.com"'),
                password=os.getenv('SUPERADMIN_PASSWORD', 'admin'),
            )

        self.create_supported_metrics()
        self.create_fake_collected_metrics()

        self.create_suported_measures()
        self.create_fake_calculated_measures()

        self.create_suported_subcharacteristics()
        self.create_fake_calculated_subcharacteristics()

        self.create_suported_characteristics()
        self.create_fake_calculated_characteristics()

        self.create_default_pre_config()

        self.create_fake_sqc_data()
