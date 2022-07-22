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
from service.collectors.github_metric_collector import GithubMetricCollector

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
        # TODO: Criar no banco as metricas suportadas pelo github
        # TODO: Elas tem thresholds e labels dinâmicas
        thd = settings.GITHUB_THRESHOLD
        #TODO: O treshold dos pipelines de build eh diferente dos outros thresholds

        models.SupportedMetric.objects.bulk_create([
            models.SupportedMetric(
                key=f"number_of_resolved_issues_in_the_last_{thd}_days",
                name=f"Number of resolved issues in the last {thd} days",
            ),
            models.SupportedMetric(
                key=f"number_of_issues_with_bug_label_in_the_last_{thd}_days",
                name=f"Number of issues with bug label in the last {thd} days",
            ),
            models.SupportedMetric(
                key=f"number_of_build_pipelines_in_the_last_{thd}_days",
                name=f"Number of build pipelines in the last {thd} days",
            ),
            models.SupportedMetric(
                key=f"runtime_sum_of_build_pipelines_in_the_last_{thd}_days",
                name=f"Runtime sum of build pipelines in the last {thd} days",
            ),
        ])

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
        # if settings.CREATE_FAKE_DATA == False:
        #     return

        qs = models.SupportedMetric.objects.annotate(
            collected_qty=Count('collected_metrics')
        )

        # TODO: Adicionar uma variável de ambiente
        # que especifica o projeto que iremos coletar os dados
        date_now = dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')


        github_metric_collector = GithubMetricCollector(
            "https://github.com/fga-eps-mds/2022-1-MeasureSoftGram-Front",
            token=settings.GITHUB_TOKEN,

        )

        # TODO: Não são métricas, são medidas
        # git_metrics = {
        #     "team_throughput": github_metric_collector.get_team_throughput("", date_now),
        #     "resolved_issues_throughput":github_metric_collector.get_resolved_issues_throughput("",date_now),
        #     "issue_type_timeframe":github_metric_collector.get_issue_type_timeframe("",date_now,'feature')
        # }

        end_date = timezone.now()
        start_date = end_date - dt.timedelta(days=90)

        for supported_metric in qs:
            if supported_metric.collected_qty <= 100:
                fake_collected_metrics = []

                for _ in range(100 - supported_metric.collected_qty):
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
