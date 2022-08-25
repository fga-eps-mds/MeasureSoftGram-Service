from rest_framework import serializers
from rest_framework.reverse import reverse

from organizations.models import (
    Organization,
    Product,
    Repository,
)


class OrganizationSerializer(
    serializers.HyperlinkedModelSerializer
):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "url",
            "name",
            "key",
            "description",
            "products",
        )
        extra_kwargs = {
            "key": {"read_only": True},
        }

    def get_products(self, obj: Organization):
        """
        Retorna as URLs das products de uma organization.
        """
        products_urls = []

        for product in obj.products.all():
            url = reverse(
                "product-detail",
                kwargs={
                    "pk": product.id,
                    "organization_pk": obj.id,
                },
                request=self.context["request"],
            )
            products_urls.append(url)
        return products_urls


class ProductSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    repositories = serializers.SerializerMethodField()

    organization = serializers.HyperlinkedRelatedField(
        view_name="organization-detail",
        read_only=True,
    )

    class Meta:
        model = Product
        fields = (
            "id",
            "url",
            "name",
            "key",
            "organization",
            "description",
            "repositories",
        )
        extra_kwargs = {
            "key": {"read_only": True},
        }

    def get_url(self, obj):
        """
        Retorna a URL desse produto
        """

        return reverse(
            "product-detail",
            kwargs={
                "pk": obj.id,
                "organization_pk": obj.organization.id,
            },
            request=self.context["request"],
        )

    def get_repositories(self, obj: Product):
        """
        Retorna as URLS dos repositórios desse produto
        """
        repositories_urls = []

        for repository in obj.repositories.all():
            url = reverse(
                "repository-detail",
                kwargs={
                    "pk": repository.id,
                    "product_pk": obj.id,
                    "organization_pk": obj.organization.id,
                },
                request=self.context["request"],
            )
            repositories_urls.append(url)
        return repositories_urls


class RepositorySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()

    class Meta:
        model = Repository
        fields = (
            "id",
            "url",
            "name",
            "key",
            "description",
            "product",
        )
        extra_kwargs = {
            "key": {"read_only": True},
        }

    def get_url(self, obj: Repository):
        """
        Gera a URL desse repositório
        """

        return reverse(
            "repository-detail",
            kwargs={
                "pk": obj.id,
                "organization_pk": obj.product.organization.id,
                "product_pk": obj.product.id,
            },
            request=self.context["request"],
        )

    def get_product(self, obj: Repository):
        """
        Gera a URL do produto desse repositório
        """

        return reverse(
            "product-detail",
            kwargs={
                "pk": obj.product.id,
                "organization_pk": obj.product.organization.id,
            },
            request=self.context["request"],
        )
