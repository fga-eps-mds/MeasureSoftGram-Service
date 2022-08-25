from rest_framework import viewsets
from rest_framework.generics import get_object_or_404

from organizations import models
from organizations import serializers


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = models.Organization.objects.all()
    serializer_class = serializers.OrganizationSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductSerializer

    def perform_create(self, serializer):
        organization = get_object_or_404(
            models.Organization,
            id=self.kwargs['organization_pk'],
        )
        serializer.save(organization=organization)


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = models.Repository.objects.all()
    serializer_class = serializers.RepositorySerializer

    def perform_create(self, serializer):
        product = get_object_or_404(
            models.Product,
            id=self.kwargs['product_pk'],
        )
        serializer.save(product=product)
