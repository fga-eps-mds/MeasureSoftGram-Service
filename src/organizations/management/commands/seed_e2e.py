"""
Management command: seed_e2e

Dados fixos para o E2E de sistema (Front + Service + Postgres reais): sempre os mesmos nomes e valores,
sem `random`, para os testes conferirem números na tela. Pode rodar várias vezes: recria só os dados da
organização E2E.

Cria:
  - usuário com senha (login por /api/v1/accounts/login/, sem OAuth), credenciais por E2E_USERNAME,
    E2E_EMAIL e E2E_PASSWORD;
  - organização, produto e repositório E2E;
  - uma análise em cada um dos dias de ANALYSIS_DAYS_AGO, com TSQMI, características, subcaracterísticas,
    medidas e métricas de valores fixos (VALUES);
  - uma release planejada (de 30 dias atrás a 30 dias à frente) com a goal padrão da pré-configuração.

As datas são relativas ao dia em que o seed roda (12h UTC), para a release e o "últimos 7 dias" valerem.

Uso:
    python manage.py seed_e2e
"""

import datetime as dt
import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from math_model.models import QualityAnalysis
from django.db import transaction

from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from goals.models import Equalizer, Goal
from measures.models import CalculatedMeasure
from metrics.models import CollectedMetric
from organizations.models import Organization, Product, Repository
from releases.models import Release
from subcharacteristics.models import CalculatedSubCharacteristic
from tsqmi.models import TSQMI

ORGANIZATION_KEY = "e2e-org"
ORGANIZATION_NAME = "E2E Org"
PRODUCT_NAME = "E2E Produto"
REPOSITORY_NAME = "e2e-repo"
RELEASE_NAME = "E2E Release 1"

# Uma análise em cada dia (dias atrás), da mais antiga para a mais recente; a última fica nos últimos 7 dias.
ANALYSIS_DAYS_AGO = (28, 21, 14, 7, 1)

# Valores por análise, na ordem de ANALYSIS_DAYS_AGO. Subcaracterísticas e medidas repetem o valor da
# característica a que pertencem; métricas também (as de contagem multiplicadas por 100).
VALUES = {
    "tsqmi": (0.50, 0.55, 0.60, 0.65, 0.70),
    "reliability": (0.40, 0.50, 0.60, 0.70, 0.80),
    "maintainability": (0.80, 0.75, 0.70, 0.65, 0.60),
    "functional_suitability": (0.30, 0.40, 0.50, 0.60, 0.70),
}


def today_noon():
    return timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)


def analysis_dates():
    return [today_noon() - dt.timedelta(days=days) for days in ANALYSIS_DAYS_AGO]


def e2e_credentials():
    return (
        os.getenv("E2E_USERNAME", "e2e"),
        os.getenv("E2E_EMAIL", "e2e@msgram.local"),
        os.getenv("E2E_PASSWORD", "e2e-senha"),
    )


class Command(BaseCommand):
    help = "Cria os dados fixos do E2E de sistema (usuário, organização, produto, repositório, análises e release)"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # metodologia (métricas, medidas, características suportadas): idempotente
        call_command("load_initial_data", stdout=self.stdout)

        user = self.create_user()
        repository = self.create_repository(user)
        release = self.create_release(repository, user)
        self.create_analyses(repository, release)

        username = e2e_credentials()[0]
        self.stdout.write(
            self.style.SUCCESS(
                f"seed_e2e: {ORGANIZATION_NAME} / {PRODUCT_NAME} / {REPOSITORY_NAME}, usuário {username}"
            )
        )

    def create_user(self):
        username, email, password = e2e_credentials()
        user, _ = get_user_model().objects.get_or_create(username=username, defaults={"email": email})
        user.email = email
        user.set_password(password)
        user.save()
        return user

    def create_repository(self, user):
        organization, _ = Organization.objects.get_or_create(
            key=ORGANIZATION_KEY,
            defaults={"name": ORGANIZATION_NAME, "description": "Organização do E2E de sistema."},
        )
        organization.admin = user
        organization.save()
        organization.members.add(user)

        product, _ = Product.objects.get_or_create(
            name=PRODUCT_NAME,
            organization=organization,
            defaults={"description": "Produto do E2E de sistema."},
        )
        repository, _ = Repository.objects.get_or_create(
            name=REPOSITORY_NAME,
            product=product,
            defaults={"description": "Repositório do E2E de sistema."},
        )
        return repository

    def create_analyses(self, repository, release):
        repository.quality_analyses.all().delete()
        dates = analysis_dates()
        analyses = {
            date: QualityAnalysis.objects.create(
                repository=repository,
                release=release,
                created_at=date,
                release_configuration=repository.product.release_configuration.first(),
            )
            for date in dates
        }
        TSQMI.objects.bulk_create(
            TSQMI(value=value, created_at=date, repository=repository, analysis=analyses[date])
            for date, value in zip(dates, VALUES["tsqmi"])
        )

        characteristics = (
            SupportedCharacteristic.objects.filter(key__in=VALUES)
            .order_by("key")
            .prefetch_related("subcharacteristics__measures__metrics")
        )
        for characteristic in characteristics:
            for date, value in zip(dates, VALUES[characteristic.key]):
                self.create_tree(repository, characteristic, date, value, analyses[date])

    def create_tree(self, repository, characteristic, date, value, analysis):
        common = {"analysis": analysis, "value": value, "created_at": date, "repository": repository}
        CalculatedCharacteristic.objects.create(characteristic=characteristic, **common)
        for subcharacteristic in characteristic.subcharacteristics.all():
            CalculatedSubCharacteristic.objects.create(subcharacteristic=subcharacteristic, **common)
            for measure in subcharacteristic.measures.all():
                CalculatedMeasure.objects.create(measure=measure, **common)
                for metric in measure.metrics.all():
                    metric_value = value if metric.metric_type == "PERCENT" else round(value * 100)
                    CollectedMetric.objects.get_or_create(
                        analysis=analysis,
                        metric=metric,
                        repository=repository,
                        created_at=date,
                        defaults={"value": metric_value, "qualifier": "TRK", "path": None},
                    )

    def create_release(self, repository, user):
        product = repository.product
        Goal.objects.filter(product=product).delete()  # cascata apaga as releases antigas do produto

        pre_config = product.release_configuration.first()
        goal = Goal.objects.create(
            data=Equalizer(pre_config.get_characteristics_keys()).get_goal(),
            created_by=user,
            product=product,
        )
        noon = today_noon()
        release = Release.objects.create(
            release_name=RELEASE_NAME,
            start_at=noon - dt.timedelta(days=30),
            end_at=noon + dt.timedelta(days=30),
            description="Release planejada do E2E de sistema.",
            created_by=user,
            product=product,
            goal=goal,
        )
        release.repositories.add(repository)
        return release
