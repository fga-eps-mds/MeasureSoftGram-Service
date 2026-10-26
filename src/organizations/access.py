import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from organizations.models import Repository, RepositoryAccess

logger = logging.getLogger(__name__)

ACCESS_TTL = timedelta(minutes=10)


def is_member(user, organization):
    return organization.members.filter(pk=user.pk).exists()


def fresh_access_q(user, prefix=""):
    """
    Filtro dos acessos do provedor ainda válidos (checados há menos de `ACCESS_TTL`). `prefix` leva o filtro
    até o `accesses` a partir do modelo consultado (ex.: `repositories__`); usuário e data ficam no mesmo
    `Q`, para valerem para o mesmo acesso.
    """
    return Q(**{f"{prefix}accesses__user": user, f"{prefix}accesses__checked_at__gte": timezone.now() - ACCESS_TTL})


def refresh_expired_accesses(user):
    """
    Revalida no provedor os acessos vencidos do usuário: os que o provedor ainda libera voltam a valer e os
    revogados são apagados. Sem isso as listagens esconderiam o repositório 10 minutos depois do login.
    """
    from organizations.utils import refresh_repository_access

    expired = RepositoryAccess.objects.filter(user=user, checked_at__lt=timezone.now() - ACCESS_TTL)
    platforms = set(expired.values_list("repository__platform", flat=True))
    if platforms:
        refresh_repository_access(user, platforms)


def visible_repositories(product, user):
    """Repositórios do produto que o usuário vê: todos para membros, só os liberados pelo provedor aos demais."""
    repositories = product.repositories.all()
    if is_member(user, product.organization):
        return repositories
    return repositories.filter(fresh_access_q(user))


def _provider_token(user, platform):
    return user.github_access_token if platform == "github" else user.gitlab_access_token


def provider_grants_access(user, repository):
    """Pergunta ao provedor, com o token do usuário, se ele enxerga o repositório."""
    platform = repository.platform
    token = _provider_token(user, platform)
    if not token:
        return False

    if platform == "github" and repository.github_full_name:
        url = f"https://api.github.com/repos/{repository.github_full_name}"
        headers = {"Authorization": f"token {token}", "Accept": "application/json"}
    elif platform == "gitlab" and repository.gitlab_project_id:
        url = f"https://gitlab.com/api/v4/projects/{repository.gitlab_project_id}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    else:
        return False

    try:
        response = requests.get(url, headers=headers, timeout=getattr(settings, "GITHUB_TIMEOUT", 10))
    except requests.exceptions.RequestException as exc:
        logger.warning("Falha ao checar acesso no provedor para %s: %s", repository, exc)
        return False
    return response.status_code == 200


def has_repository_access(user, repository):
    """Acesso de leitura via provedor: usa o `RepositoryAccess` recente ou renova a checagem; apaga se revogado."""
    access = RepositoryAccess.objects.filter(user=user, repository=repository).first()
    if access and timezone.now() - access.checked_at < ACCESS_TTL:
        return True

    if provider_grants_access(user, repository):
        RepositoryAccess.objects.update_or_create(
            user=user, repository=repository, defaults={"checked_at": timezone.now()}
        )
        return True

    if access:
        access.delete()
    return False


def find_repository(org_pk, prod_pk, repo_pk):
    return Repository.objects.filter(id=repo_pk, product_id=prod_pk, product__organization_id=org_pk).first()
