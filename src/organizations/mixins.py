from django.db.models import Q
from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import SAFE_METHODS

from organizations.access import (
    find_repository,
    fresh_access_q,
    has_repository_access,
    refresh_expired_accesses,
    visible_repositories,
)
from organizations.models import Organization, Product, Repository


class UserScopedMixin:
    """
    Mixin to enforce that querysets and objects are restricted to organizations
    where request.user is a member.

    Em leitura, quem tem acesso a um repositório no provedor (`RepositoryAccess`) também enxerga
    esse repositório, o produto e a organização dele. Escrita exige ser membro.
    """

    def _read_only_request(self):
        return self.request.method in SAFE_METHODS

    def _refresh_provider_accesses(self):
        """Revalida os acessos vencidos uma vez por requisição, antes de qualquer listagem de leitura."""
        if not getattr(self.request, "_provider_accesses_refreshed", False):
            self.request._provider_accesses_refreshed = True
            refresh_expired_accesses(self.request.user)

    def get_user_organizations(self):
        user = self.request.user
        if not self._read_only_request():
            return Organization.objects.filter(members=user)
        self._refresh_provider_accesses()
        return Organization.objects.filter(
            Q(members=user) | fresh_access_q(user, "products__repositories__")
        ).distinct()

    def get_user_products(self):
        user = self.request.user
        if not self._read_only_request():
            return Product.objects.filter(organization__members=user)
        self._refresh_provider_accesses()
        return Product.objects.filter(
            Q(organization__members=user) | fresh_access_q(user, "repositories__")
        ).distinct()

    def get_user_repositories(self):
        user = self.request.user
        if not self._read_only_request():
            return Repository.objects.filter(product__organization__members=user)
        self._refresh_provider_accesses()
        return Repository.objects.filter(
            Q(product__organization__members=user) | fresh_access_q(user)
        ).distinct()

    def get_visible_repositories(self, product):
        """Repositórios do produto que o usuário pode ver: todos para membros, só os liberados aos demais."""
        return visible_repositories(product, self.request.user)

    def get_organization(self):
        org_pk = self.kwargs.get("organization_pk") or self.kwargs.get("pk")
        return get_object_or_404(self.get_user_organizations(), id=org_pk)

    def get_product(self):
        org_pk = self.kwargs.get("organization_pk")
        prod_pk = self.kwargs.get("product_pk") or self.kwargs.get("pk")
        products = self.get_user_products().filter(organization_id=org_pk).select_related("organization")
        return get_object_or_404(products, id=prod_pk)

    def get_repository(self):
        org_pk = self.kwargs.get("organization_pk")
        prod_pk = self.kwargs.get("product_pk")
        repo_pk = self.kwargs.get("repository_pk") or self.kwargs.get("pk")
        member_repositories = Repository.objects.filter(
            product__organization__members=self.request.user,
            product_id=prod_pk,
            product__organization_id=org_pk,
        )
        member_repository = member_repositories.filter(id=repo_pk).first()
        if member_repository:
            return member_repository

        # Não é membro: só leitura, e só se o provedor ainda libera o repositório.
        repository = find_repository(org_pk, prod_pk, repo_pk)
        if repository is None:
            raise Http404
        if not self._read_only_request():
            raise PermissionDenied("Acesso somente leitura a este repositório.")
        if not has_repository_access(self.request.user, repository):
            raise Http404
        return repository
