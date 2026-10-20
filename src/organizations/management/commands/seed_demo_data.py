"""
Management command: seed_demo_data

Popula o banco com dados ricos para os dashboards do produto:
  - 180 dias de histórico diário para cada entidade do modelo
  - Tendências realistas (melhora/piora + ruído)
  - Releases trimestrais com datas reais
  - Goals por produto linkados ao admin
  - TSQMI com timestamps corretos e evolução coerente
  - Métricas por arquivo para análise de distribuição estatística
  - Garante que TODAS as características sejam criadas para CADA data (evita NULL)

IMPORTANTE: Este seed popula dados para os seguintes dashboards:
  1. Visão Geral de Qualidade
  2. Pulso de Qualidade (TSQMI)
  3. Evolução Temporal
  4. Evolução das características na tela do repositório

Uso:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --days 365
    python manage.py seed_demo_data --repos "MeasureSoftGram-Service,MeasureSoftGram-Front"
    python manage.py seed_demo_data --clean-all  # Limpa e recria todos os dados
"""

import datetime as dt
import math
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from characteristics.models import CalculatedCharacteristic, SupportedCharacteristic
from goals.models import Goal
from measures.models import CalculatedMeasure, SupportedMeasure
from metrics.models import CollectedMetric, SupportedMetric
from organizations.models import Product, Repository
from release_configuration.models import ReleaseConfiguration
from releases.models import Release
from subcharacteristics.models import CalculatedSubCharacteristic, SupportedSubCharacteristic
from tsqmi.models import TSQMI

User = get_user_model()

# Perfis de tendência: (slope_per_day, noise_amplitude, baseline)
# slope positivo = melhora ao longo do tempo
TREND_PROFILES = {
    "improving": dict(slope=0.0008, noise=0.06, base=0.45),
    "declining": dict(slope=-0.0006, noise=0.06, base=0.75),
    "stable": dict(slope=0.0001, noise=0.04, base=0.60),
    "volatile": dict(slope=0.0002, noise=0.12, base=0.55),
    "recovering": dict(slope=0.0010, noise=0.07, base=0.30),
}

REPO_PROFILES = {
    "2022-1-MeasureSoftGram-Service": "improving",
    "2022-1-MeasureSoftGram-Front": "volatile",
    "2022-1-MeasureSoftGram-Core": "stable",
    "2022-1-MeasureSoftGram-CLI": "declining",
    "2021.1_G01_Animalesco_BackEnd": "recovering",
    "2021.1_G01_Animalesco_FrontEnd": "stable",
    "2019.2-Acacia": "improving",
    "2019.2-Acacia-Frontend": "declining",
    "2020.1-BCE": "volatile",
}


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def _trend_value(day_idx: int, profile_name: str, char_offset: float = 0.0) -> float:
    p = TREND_PROFILES[profile_name]
    base = _clamp(p["base"] + char_offset)
    linear = p["slope"] * day_idx
    wave = 0.03 * math.sin(2 * math.pi * day_idx / 30)  # ciclo mensal
    noise = random.gauss(0, p["noise"])
    return _clamp(base + linear + wave + noise)


def _make_timestamps(days: int, end: dt.datetime) -> list[dt.datetime]:
    """Gera um timestamp por dia (com hora aleatória)."""
    return [
        end
        - dt.timedelta(
            days=days - i,
            hours=random.randint(0, 8),
            minutes=random.randint(0, 59),
        )
        for i in range(days)
    ]


class Command(BaseCommand):
    help = "Popula banco com dados ricos para os dashboards do produto"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=180, help="Dias de histórico")
        parser.add_argument(
            "--repos",
            type=str,
            default="",
            help="Nomes de repositórios separados por vírgula (vazio = todos)",
        )
        parser.add_argument(
            "--clean-tsqmi",
            action="store_true",
            default=False,
            help="Apaga os TSQMI sem timestamps corretos antes de recriar",
        )
        parser.add_argument(
            "--clean-all",
            action="store_true",
            default=False,
            help="Apaga TODOS os dados de características calculadas antes de recriar (corrige valores NULL)",
        )

    def handle(self, *args, **kwargs):
        self.days = kwargs["days"]
        self.clean_tsqmi = kwargs["clean_tsqmi"]
        self.clean_all = kwargs["clean_all"]
        repo_filter = [r.strip() for r in kwargs["repos"].split(",") if r.strip()]

        self.admin = User.objects.filter(is_superuser=True).first()
        if not self.admin:
            self.stderr.write("Nenhum superuser encontrado. Rode load_initial_data primeiro.")
            return

        self.end_date = timezone.now()
        self.start_date = self.end_date - dt.timedelta(days=self.days)

        repos = Repository.objects.all()
        if repo_filter:
            repos = repos.filter(name__in=repo_filter)

        # Limpeza global se solicitado
        if self.clean_all:
            self.stdout.write(self.style.WARNING("Limpando TODOS os dados de características calculadas..."))
            deleted = CalculatedCharacteristic.objects.filter(repository__in=repos).delete()
            self.stdout.write(f"  → {deleted[0]} características calculadas removidas")

            deleted_measures = CalculatedMeasure.objects.filter(repository__in=repos).delete()
            self.stdout.write(f"  → {deleted_measures[0]} medidas calculadas removidas")

            deleted_subchars = CalculatedSubCharacteristic.objects.filter(repository__in=repos).delete()
            self.stdout.write(f"  → {deleted_subchars[0]} subcaracterísticas calculadas removidas")

            deleted_metrics = CollectedMetric.objects.filter(repository__in=repos).delete()
            self.stdout.write(f"  → {deleted_metrics[0]} métricas coletadas removidas")
            self.stdout.write("")

        self.stdout.write(f"Populando {repos.count()} repositórios com {self.days} dias de histórico...")

        for repo in repos:
            profile = REPO_PROFILES.get(repo.name, "stable")
            self.stdout.write(f"  → {repo.name} [{profile}]")
            self._seed_repo(repo, profile)

        self.stdout.write("")
        self._seed_goals_and_releases()

        self.stdout.write(self.style.SUCCESS("✓ seed_demo_data concluído."))

    # ------------------------------------------------------------------
    # Por repositório
    # ------------------------------------------------------------------

    def _seed_repo(self, repo: Repository, profile: str):
        # Gera timestamps para todo o período
        all_timestamps = _make_timestamps(self.days, self.end_date)

        # IMPORTANTE: Para o pulso ECG funcionar, características e TSQMI devem estar nas MESMAS datas
        # Seleciona 10 timestamps espaçados uniformemente (incluindo o mais recente) para
        # TSQMI e características — o painel "Planejado vs Realizado" só considera os
        # últimos 7 dias, então a última amostra precisa ficar perto de `self.end_date`.
        TSQMI_MEASUREMENTS = 10
        last_idx = len(all_timestamps) - 1
        indices = [round(i * last_idx / (TSQMI_MEASUREMENTS - 1)) for i in range(TSQMI_MEASUREMENTS)]
        tsqmi_timestamps = [all_timestamps[i] for i in indices]

        if self.clean_tsqmi:
            TSQMI.objects.filter(repository=repo).delete()

        self._seed_collected_metrics(repo, all_timestamps)
        self._seed_calculated_measures(repo, profile, all_timestamps)
        self._seed_calculated_subchars(repo, profile, all_timestamps)
        # Criar características APENAS nas datas dos TSQMIs (10 datas)
        self._seed_calculated_chars(repo, profile, tsqmi_timestamps)
        self._seed_tsqmi(repo, profile, tsqmi_timestamps)

    def _seed_collected_metrics(self, repo: Repository, timestamps: list):
        """
        Cria métricas coletadas por arquivo, um conjunto por dia.
        Gera ~10 arquivos por dia para ter distribuição estatística.
        """
        metrics = list(SupportedMetric.objects.all())
        if not metrics:
            return

        # Limita a geração de métricas de arquivo para não explodir o banco
        DAYS_TO_SEED = min(len(timestamps), 30)
        sampled_timestamps = timestamps[-DAYS_TO_SEED:]

        FILE_PATHS = [
            f"src/{module}/{fname}"
            for module in ["api", "models", "services", "utils", "tests"]
            for fname in ["main.py", "helper.py", "core.py"]
        ]

        to_create = []
        for ts in sampled_timestamps:
            for metric in metrics[:8]:  # métricas principais
                for path in random.sample(FILE_PATHS, k=min(8, len(FILE_PATHS))):
                    qualifier = "FIL" if "test" not in path else "UTS"
                    to_create.append(
                        CollectedMetric(
                            metric=metric,
                            value=(
                                random.uniform(0, 1) if metric.metric_type == "PERCENT" else random.uniform(0, 100)
                            ),
                            path=path,
                            qualifier=qualifier,
                            created_at=ts,
                            repository=repo,
                        )
                    )

        if to_create:
            CollectedMetric.objects.bulk_create(to_create, batch_size=500, ignore_conflicts=False)
            self.stdout.write(f"    CollectedMetric: +{len(to_create)}")

    def _seed_calculated_measures(self, repo: Repository, profile: str, timestamps: list):
        measures = list(SupportedMeasure.objects.all())
        if not measures:
            return

        to_create = []
        for i, ts in enumerate(timestamps):
            for j, measure in enumerate(measures):
                offset = (j - len(measures) / 2) * 0.05
                to_create.append(
                    CalculatedMeasure(
                        measure=measure,
                        value=_trend_value(i, profile, char_offset=offset),
                        created_at=ts,
                        repository=repo,
                    )
                )

        CalculatedMeasure.objects.bulk_create(to_create, batch_size=1000)
        self.stdout.write(f"    CalculatedMeasure: +{len(to_create)}")

    def _seed_calculated_subchars(self, repo: Repository, profile: str, timestamps: list):
        subchars = list(SupportedSubCharacteristic.objects.all())
        if not subchars:
            return

        to_create = []
        for i, ts in enumerate(timestamps):
            for j, subchar in enumerate(subchars):
                offset = (j - len(subchars) / 2) * 0.04
                to_create.append(
                    CalculatedSubCharacteristic(
                        subcharacteristic=subchar,
                        value=_trend_value(i, profile, char_offset=offset),
                        created_at=ts,
                        repository=repo,
                    )
                )

        CalculatedSubCharacteristic.objects.bulk_create(to_create, batch_size=1000)
        self.stdout.write(f"    CalculatedSubChar: +{len(to_create)}")

    def _seed_calculated_chars(self, repo: Repository, profile: str, timestamps: list):
        """
        Cria características calculadas usando exatamente os timestamps fornecidos.

        IMPORTANTE: Os timestamps devem ser os mesmos usados para criar os TSQMIs,
        garantindo que o dashboard de pulso ECG funcione corretamente (sem valores NULL).
        """
        chars = list(SupportedCharacteristic.objects.all())
        if not chars:
            return

        # IMPORTANTE: Garantir que temos exatamente 3 características
        # Se não tivermos, o dashboard terá valores NULL
        if len(chars) != 3:
            self.stderr.write(
                f"AVISO: Esperado 3 características, mas encontrado {len(chars)}. "
                f"Isso pode causar valores NULL no dashboard!"
            )

        # Cada característica tem sua própria "personalidade" de tendência
        char_profiles = {
            "reliability": ("improving", 0.0),
            "maintainability": ("declining", 0.05),
            "functional_suitability": ("stable", -0.05),
        }

        to_create = []
        for i, ts in enumerate(timestamps):
            # Usar índice proporcional para manter a progressão da tendência
            # Mapeia o índice atual para o intervalo completo de dias
            day_idx = int((i / len(timestamps)) * self.days)

            # Criar TODAS as características para CADA timestamp
            # Isso evita valores NULL no dashboard quando agrupamos por data
            for char in chars:
                sub_profile, offset = char_profiles.get(char.key, (profile, 0.0))
                to_create.append(
                    CalculatedCharacteristic(
                        characteristic=char,
                        value=_trend_value(day_idx, sub_profile, char_offset=offset),
                        created_at=ts,
                        repository=repo,
                    )
                )

        CalculatedCharacteristic.objects.bulk_create(to_create, batch_size=1000)
        expected = len(timestamps) * len(chars)
        actual = len(to_create)
        if expected != actual:
            self.stderr.write(
                f"AVISO: Esperado criar {expected} registros ({len(timestamps)} datas × {len(chars)} chars), "
                f"mas criou {actual}!"
            )
        self.stdout.write(
            f"    CalculatedChar: +{len(to_create)} ({len(timestamps)} datas × {len(chars)} chars = PAREADO COM TSQMI)"
        )

    def _seed_tsqmi(self, repo: Repository, profile: str, timestamps: list):
        """
        Cria TSQMIs usando exatamente os timestamps fornecidos.

        IMPORTANTE: Os timestamps devem ser os mesmos usados para criar as características
        calculadas, garantindo que o dashboard de pulso ECG funcione corretamente.
        """
        if self.clean_tsqmi:
            existing = 0
        else:
            existing = TSQMI.objects.filter(repository=repo).count()

        # Usar exatamente os timestamps fornecidos
        TSQMI_MEASUREMENTS = len(timestamps)

        if existing >= TSQMI_MEASUREMENTS:
            self.stdout.write(f"    TSQMI: já tem {existing} registros, pulando")
            return

        to_create = []
        for i, ts in enumerate(timestamps):
            # Usar índice proporcional para manter a progressão da tendência
            # Mapeia o índice atual para o intervalo completo de dias
            day_idx = int((i / len(timestamps)) * self.days)
            to_create.append(
                TSQMI(
                    value=_trend_value(day_idx, profile),
                    created_at=ts,
                    repository=repo,
                )
            )

        TSQMI.objects.bulk_create(to_create, batch_size=500)
        self.stdout.write(
            f"    TSQMI: +{len(to_create)} ({TSQMI_MEASUREMENTS} medições nas MESMAS datas das características)"
        )

    # ------------------------------------------------------------------
    # Goals e Releases
    # ------------------------------------------------------------------

    def _seed_goals_and_releases(self):
        self.stdout.write("Criando Goals e Releases...")

        products = Product.objects.all()
        chars = list(SupportedCharacteristic.objects.values_list("key", flat=True))

        for product in products:
            pre_config = product.release_configuration.first()
            if not pre_config:
                continue

            # 4 releases trimestrais cobrindo os últimos `self.days` dias
            quarter = self.days // 4
            for q in range(4):
                start_at = self.end_date - dt.timedelta(days=self.days - q * quarter)
                end_at = start_at + dt.timedelta(days=quarter)
                release_name = f"v{2025 + q // 4}.{q % 4 + 1}.0"

                # Goal com pesos aleatórios para este release
                goal_data = self._build_goal_data(pre_config)
                goal = Goal.objects.create(
                    data=goal_data,
                    created_by=self.admin,
                    product=product,
                )

                Release.objects.get_or_create(
                    release_name=release_name,
                    product=product,
                    defaults=dict(
                        start_at=start_at,
                        end_at=end_at,
                        created_by=self.admin,
                        goal=goal,
                        description=f"Release trimestral {release_name} do produto {product.name}",
                    ),
                )

        goals_count = Goal.objects.count()
        releases_count = Release.objects.count()
        self.stdout.write(f"  Goals: {goals_count}  |  Releases: {releases_count}")

    def _build_goal_data(self, pre_config: ReleaseConfiguration) -> dict:
        """Gera um dicionário de pesos aleatórios válido para o equalizador."""
        from goals.models import Equalizer

        chars_keys = pre_config.get_characteristics_keys()
        equalizer = Equalizer(chars_keys)

        # Aplica entre 3 e 8 mudanças aleatórias de delta
        for _ in range(random.randint(3, 8)):
            key = random.choice(chars_keys)
            delta = random.randint(-20, 20)
            try:
                equalizer.update(key, delta)
            except Exception:
                pass

        return equalizer.get_goal()
