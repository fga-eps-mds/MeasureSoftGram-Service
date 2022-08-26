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
    latest_values = serializers.SerializerMethodField()
    historical_values = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    class Meta:
        model = Repository
        fields = (
            "id",
            "url",
            "name",
            "key",
            "description",
            "product",
            "latest_values",
            "historical_values",
            "actions",
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

    def reverse_repository_resource(self, obj: Repository, viewname: str):
        return reverse(
            viewname,
            kwargs={
                "repository_pk": obj.id,
                "organization_pk": obj.product.organization.id,
                "product_pk": obj.product.id,
            },
            request=self.context["request"],
        )

    def get_actions(self, obj):
        """
        Lista todas as ações que podem ser feitas no repositório
        """

        collect_metric_url = self.reverse_repository_resource(
            obj, "collectedmetric-list"
        )

        calculate_measures_url = self.reverse_repository_resource(
            obj, "calculate-measures-list",
        )

        calculate_subcharacteristics_url = self.reverse_repository_resource(
            obj, "calculate-subcharacteristics-list",
        )

        calculate_characteristics_url = self.reverse_repository_resource(
            obj, "calculate-characteristics-list",
        )

        return {
            'collect metric': collect_metric_url,
            'calculate measures': calculate_measures_url,
            'calculate subcharacteristics': calculate_subcharacteristics_url,
            'calculate characteristics': calculate_characteristics_url,
        }

    def get_historical_values(self, obj: Repository):
        """
        Gera a URL dos valores coletados históricos desse repositório
        """
        metrics_historical_values_url = self.reverse_repository_resource(
            obj, "metrics-historical-values-list",
        )

        measures_historical_values_url = self.reverse_repository_resource(
            obj, "measures-historical-values-list",
        )

        subcharacteristics_historical_values_url = self.reverse_repository_resource(
            obj, "subcharacteristics-historical-values-list",
        )

        characteristics_historical_values_url = self.reverse_repository_resource(
            obj, "characteristics-historical-values-list",
        )

        return {
            'metrics': metrics_historical_values_url,
            'measures': measures_historical_values_url,
            'subcharacteristics': subcharacteristics_historical_values_url,
            'characteristics': characteristics_historical_values_url,
        }

    def get_latest_values(self, obj: Repository):
        """
        Gera a URL dos últimos valores coletados desse repositório
        """

        metrics_historical_values_url = self.reverse_repository_resource(
            obj, "latest-collected-metrics-list"
        )

        measures_latest_values_url = self.reverse_repository_resource(
            obj, "latest-calculated-measures-list",
        )

        subcharacteristics_latest_values_url = self.reverse_repository_resource(
            obj, "latest-calculated-subcharacteristics-list",
        )

        characteristics_latest_values_url = self.reverse_repository_resource(
            obj, "latest-calculated-characteristics-list",
        )

        return {
            'metrics': metrics_historical_values_url,
            'measures': measures_latest_values_url,
            'subcharacteristics': subcharacteristics_latest_values_url,
            'characteristics': characteristics_latest_values_url,
        }
