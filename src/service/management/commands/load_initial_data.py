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

# Local Imports
from service import models, staticfiles
from service.collectors import GithubMetricCollector
from utils import (
    get_random_datetime,
    get_random_qualifier,
    get_random_string,
    get_random_value,
)

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Registra os dados iniciais da aplicação no banco de dados"
    )

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

    def crete_fake_collected_metrics(self):
        if settings.CREATE_FAKE_DATA is False:
            return

        qs = models.SupportedMetric.objects.annotate(
            collected_qty=Count('collected_metrics')
        )

        end_date = timezone.now()
        start_date = end_date - dt.timedelta(days=90)

        MIN_NUMBER_OF_COLLECTED_METRICS = 15
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

    def handle(self, *args, **options):
        with contextlib.suppress(IntegrityError):
            User.objects.create_superuser(
                username=os.getenv('SUPERADMIN_USERNAME', 'admin'),
                email=os.getenv('SUPERADMIN_EMAIL', '"admin@admin.com"'),
                password=os.getenv('SUPERADMIN_PASSWORD', 'admin'),
            )

        self.create_supported_metrics()
        self.crete_fake_collected_metrics()
