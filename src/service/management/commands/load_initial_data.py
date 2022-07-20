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
from utils import get_random_datetime, get_random_value

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Registra os dados iniciais da aplicação no banco de dados"
    )

    def create_suported_measures(self):
        """
        Registra no banco de dados todas as medidas que o sistema tem suporte
        """
        supported_measures = [
            "passed_tests",
            "test_builds",
            "test_coverage",
            "non_complex_file_density",
            "commented_file_density",
            "duplication_absense",
        ]
        for measure in supported_measures:
            with contextlib.suppress(IntegrityError):
                name = measure.replace('_', ' ').title()
                models.SupportedMeasure.objects.create(
                    key=measure,
                    name=name,
                )

    def create_supported_metrics(self):
        sonar_endpoint = 'https://sonarcloud.io/api/metrics/search'

        request = requests.get(sonar_endpoint)

        if request.ok:
            data = request.json()
        else:
            data = staticfiles.SONARQUBE_AVAILABLE_METRICS

        for metric in data['metrics']:
            try:
                models.SupportedMetric.objects.create(
                    key=metric['key'],
                    name=metric['name'],
                    description=metric.get('description', ''),
                    metric_type=metric['type'],
                )
            except IntegrityError:
                continue

    def crete_fake_collected_metrics(self):
        # if settings.CREATE_FAKE_DATA == False:
        #     return

        qs = models.SupportedMetric.objects.annotate(
            collected_qty=Count('collected_metrics')
        )

        end_date = timezone.now()
        start_date = end_date - dt.timedelta(days=90)

        for supported_metric in qs:
            if supported_metric.collected_qty <= 100:
                fake_collected_metrics = []

                for _ in range(100 - supported_metric.collected_qty):
                    metric_type = supported_metric.metric_type

                    fake_collected_metric = models.CollectedMetric(
                        metric=supported_metric,
                        value=get_random_value(metric_type),
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

        self.create_suported_measures()
