"""Gera demonstrações pelo pipeline da Action, com cinco camadas por AQ."""

import datetime as dt

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from goals.models import Equalizer, Goal
from organizations.models import Repository
from releases.models import Release
from utils.demo_payload import demo_payload, persist_demo_analysis

ANALYSIS_EVERY_DAYS = 3
GITHUB_METRICS = ("total_issues", "resolved_issues", "sum_ci_feedback_times", "total_builds")


class Command(BaseCommand):
    help = "Gera análises completas para os repositórios selecionados, usando o Core."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=180)
        parser.add_argument("--repos", default="", help="Nomes separados por vírgula; vazio seleciona todos.")
        parser.add_argument("--clean-all", action="store_true", help="Recria AQs dos repositórios selecionados.")
        parser.add_argument(
            "--clean-tsqmi", action="store_true", help="Alias de --clean-all: preserva integridade das AQs."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        days = options["days"]
        if days < 1:
            raise CommandError("--days deve ser positivo.")
        admin = get_user_model().objects.filter(is_superuser=True).first()
        if admin is None:
            self.stderr.write("Nenhum superuser encontrado. Rode load_initial_data primeiro.")
            return
        repositories = Repository.objects.select_related("product")
        names = [name.strip() for name in options["repos"].split(",") if name.strip()]
        if names:
            repositories = repositories.filter(name__in=names)
        end = timezone.now()
        offsets = sorted(set(range(1, days + 1, ANALYSIS_EVERY_DAYS)) | {days}, reverse=True)
        for repository in repositories:
            if options["clean_all"] or options["clean_tsqmi"]:
                repository.quality_analyses.all().delete()
            elif repository.quality_analyses.exists():
                continue
            configuration = repository.product.release_configuration.first()
            # Não criar releases sobrepostas em produtos que já têm planejamento.
            if not Release.objects.filter(product=repository.product).exists():
                goal = Goal.objects.create(
                    product=repository.product,
                    created_by=admin,
                    data=Equalizer(configuration.get_characteristics_keys()).get_goal(),
                )
                Release.objects.create(
                    product=repository.product,
                    created_by=admin,
                    goal=goal,
                    release_name="Demonstração",
                    start_at=end - dt.timedelta(days=days + 1),
                    end_at=end,
                )
            for index, offset in enumerate(offsets):
                payload = demo_payload(index)
                values = (10 + 3 * index, 8 + 2 * index, 300 + 60 * index, 5 + index)
                for metric, value in zip(payload["github"]["metrics"], values):
                    metric["value"] = value
                persist_demo_analysis(repository, end - dt.timedelta(days=offset), payload)
            self.stdout.write(f"{repository.name}: {len(offsets)} análises completas.")
        self.stdout.write(self.style.SUCCESS("seed_demo_data concluído."))
