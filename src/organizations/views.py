from rest_framework import mixins, viewsets
from rest_framework import viewsets
from rest_framework.generics import get_object_or_404

from organizations.models import (
    Organization,
    Product,
    Repository,
)

from organizations.serializers import (
    OrganizationSerializer,
    ProductSerializer,
    RepositorySerializer,
    RepositorySQCLatestValueSerializer,
    RepositoriesSQCHistorySerializer,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def perform_create(self, serializer):
        organization = get_object_or_404(
            Organization,
            id=self.kwargs['organization_pk'],
        )
        serializer.save(organization=organization)


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer

    def perform_create(self, serializer):
        product = get_object_or_404(
            Product,
            id=self.kwargs['product_pk'],
        )
        serializer.save(product=product)


class RepositoriesSQCLatestValueViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = RepositorySQCLatestValueSerializer

    def get_queryset(self):
        product = get_object_or_404(Product, id=self.kwargs['product_pk'])
        qs = Repository.objects.filter(product=product)
        qs = qs.prefetch_related(
            'calculated_sqcs',
            'product',
            'product__organization',
        )
        return qs


class RepositoriesSQCHistoryViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = RepositoriesSQCHistorySerializer

    def get_queryset(self):
        product = get_object_or_404(Product, id=self.kwargs['product_pk'])
        qs = Repository.objects.filter(product=product)
        qs = qs.prefetch_related(
            'calculated_sqcs',
            'product',
            'product__organization',
        )
        return qs
