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
from utils import (
    get_random_datetime,
    get_random_qualifier,
    get_random_string,
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
                    {"key": "tests"},
                    {"key": "test_execution_time"},
                ],
            },
            {
                "key": "test_coverage",
                "metrics": [
                    {"key": "coverage"},
                    {"key": "number_of_files"},
                ],
            },
            {
                "key": "non_complex_file_density",
                "metrics": [
                    {"key": "number_of_files"},
                    {"key": "functions"},
                    {"key": "complexity"},
                ],
            },
            {
                "key": "commented_file_density",
                "metrics": [
                    {"key": "number_of_files"},
                    {"key": "comment_lines_density"},
                ],
            },
            {
                "key": "duplication_absense",
                "metrics": [
                    {"key": "number_of_files"},
                    {"key": "duplicated_lines_density"},
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

                metrics_keys = [
                    metric["key"]
                    for metric in measure_data["metrics"]
                ]

                metrics = models.SupportedMetric.objects.filter(
                    key__in=metrics_keys,
                )
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

    def create_github_supported_metrics(self):
        github_metrics = [
            models.SupportedMetric(
                key=metric['key'],
                name=metric['name'],
                metric_type=metric['metric_type'],
            ) for metric in settings.GITHUB_METRICS
        ]

        for metric in github_metrics:
            try:
                metric.save()
            except IntegrityError:
                db_metric = models.SupportedMetric.objects.get(key=metric.key)
                db_metric.metric_type = metric.metric_type
                db_metric.name = metric.name
                db_metric.save()

    def model_generator(self, model, metrics):
        for metric in metrics:
            with contextlib.suppress(IntegrityError):
                model.objects.create(
                    key=metric['key'],
                    name=metric['name'],
                    description=metric.get('description', ''),
                    metric_type=metric['type'],
                )

    def create_fake_collected_metrics(self):
        if settings.CREATE_FAKE_DATA is False:
            return

        qs = models.SupportedMetric.objects.annotate(
            collected_qty=Count('collected_metrics')
        )

        end_date = timezone.now()
        start_date = end_date - dt.timedelta(days=90)

        MIN_NUMBER_OF_COLLECTED_METRICS = 50
        MIN_METRICS = MIN_NUMBER_OF_COLLECTED_METRICS

        for supported_metric in qs:
            if supported_metric.collected_qty <= MIN_METRICS:
                fake_collected_metrics = []

                for _ in range(MIN_METRICS - supported_metric.collected_qty):
                    metric_type = supported_metric.metric_type
                    metric_value = get_random_value(metric_type)

                    # if supported_metric in git_metrics:
                    #     metric_value = git_metrics[supported_metric]

                    fake_collected_metric = models.CollectedMetric(
                        metric=supported_metric,
                        path=get_random_string(),
                        qualifier=get_random_qualifier(),
                        value=metric_value,
                        created_at=get_random_datetime(start_date, end_date),
                    )

                    fake_collected_metrics.append(fake_collected_metric)
                models.CollectedMetric.objects.bulk_create(fake_collected_metrics)

    def create_fake_calculated_measures(self):
        if settings.CREATE_FAKE_DATA is False:
            return

        qs = models.SupportedMeasure.objects.annotate(
            calculated_qty=Count('calculated_measures'),
        )

        end_date = timezone.now()
        start_date = end_date - dt.timedelta(days=90)

        MIN_NUMBER_OF_CALCULATED_MEASURES = 50
        MIN_MEASURES = MIN_NUMBER_OF_CALCULATED_MEASURES

        for supported_measure in qs:
            if supported_measure.calculated_qty <= MIN_MEASURES:
                fake_calculated_measures = []

                for _ in range(MIN_MEASURES - supported_measure.calculated_qty):
                    metric_value = get_random_value('PERCENT')

                    fake_calculated_measure = models.CalculatedMeasure(
                        measure=supported_measure,
                        value=metric_value,
                        created_at=get_random_datetime(start_date, end_date),
                    )
                    fake_calculated_measures.append(fake_calculated_measure)
                models.CalculatedMeasure.objects.bulk_create(fake_calculated_measures)

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
                sub_char, _ = models.SupportedSubCharacteristic.objects.get_or_create(
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

        for characteristic in suported_characteristics:
            with contextlib.suppress(IntegrityError):
                charact, _ = models.SupportedCharacteristic.objects.get_or_create(
                    name=characteristic['name'],
                    key=characteristic['key'],
                )

                subcharacteristics_keys = [
                    subcharacteristic["key"]
                    for subcharacteristic in characteristic["subcharacteristics"]
                ]

                subcharacteristics = models.SupportedSubCharacteristic.objects.filter(
                    key__in=subcharacteristics_keys,
                )

                charact.subcharacteristics.set(subcharacteristics)

    def create_default_pre_config(self):
        with contextlib.suppress(IntegrityError):
            models.PreConfig.objects.create(
                name='Default pre-config',
                data=staticfiles.DEFAULT_ṔRE_CONFIG,
            )

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
        self.create_suported_characteristics()

        self.create_default_pre_config()
