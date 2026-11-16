"""Associação de execuções e consultas por identidade da análise."""

from django.db.models import Q
from django.utils import timezone

from math_model.models import QualityAnalysis
from releases.models import Release
from utils.exceptions import CalculateModelException


def resolve_active_release(repository, at=None):
    day = timezone.localdate(at or timezone.now())
    releases = list(
        Release.objects.filter(product_id=repository.product_id, start_at__date__lte=day, end_at__date__gte=day)
        .filter(Q(repositories=repository) | Q(repositories__isnull=True))
        .distinct()[:2]
    )
    if len(releases) > 1:
        raise CalculateModelException("Mais de uma release ativa para este repositório.")
    return releases[0] if releases else None


def get_latest_release_analyses(release, repository_ids):
    return (
        QualityAnalysis.objects.filter(release=release, repository_id__in=repository_ids)
        .order_by("repository_id", "-created_at", "-id")
        .distinct("repository_id")
    )


def get_release_analyses_history(release, repository_ids):
    return QualityAnalysis.objects.filter(release=release, repository_id__in=repository_ids).order_by(
        "created_at", "id"
    )


def filter_release_analyses(queryset, release):
    return queryset.filter(analysis__release=release)


def latest_analysis_records(queryset, release, repository_ids):
    return queryset.filter(analysis_id__in=get_latest_release_analyses(release, repository_ids).values("id"))
