from django.conf import settings
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueValidator

from organizations.models import Organization, Product, Repository
from sqc.models import SQC
from sqc.serializers import SQCSerializer


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    products = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "url",
            "name",
            "key",
            "description",
            "products",
            "actions",
        )
        extra_kwargs = {
            "key": {"read_only": True},
            "name": {
                "validators": [
                    UniqueValidator(
                        queryset=Organization.objects.all(),
                        message="Organization with this name already exists.",
                    )
                ]
            }
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

    def get_actions(self, obj: Organization):
        """
        Retorna as URLs das actions de uma organization.
        """
        create_a_new_product_url = reverse(
            "product-list",
            kwargs={
                "organization_pk": obj.id,
            },
            request=self.context["request"],
        )

        return {
            'create a new product': create_a_new_product_url,
        }


class ProductSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    repositories = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

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
            "actions",
        )
        extra_kwargs = {
            "key": {"read_only": True},
        }

    def validate(self, attrs):
        """
        Valida se o nome do produto é único para a organização
        """
        name = attrs["name"]
        organization = self.context["view"].get_organization()

        qs = Product.objects.filter(name=name, organization=organization)

        if qs.exists():
            raise serializers.ValidationError(
                "Product with this name already exists."
            )

        return attrs

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

    def reverse_product_resource(self, obj: Product, viewname: str):
        return reverse(
            viewname,
            kwargs={
                "product_pk": obj.id,
                "organization_pk": obj.organization.id,
            },
            request=self.context["request"],
        )

    def get_actions(self, obj: Product):
        """
        Retorna o valor atuais das entidades associadas a um produto
        """
        create_a_new_repository_url = self.reverse_product_resource(
            obj, "repository-list"
        )

        current_goal_url = self.reverse_product_resource(
            obj, "current-goal-list"
        )

        compare_goals_url = self.reverse_product_resource(
            obj, "all-goal-list"
        )

        create_a_new_goal_url = self.reverse_product_resource(
            obj, "create-goal-list"
        )

        current_pre_config_url = self.reverse_product_resource(
            obj, "current-pre-config-list"
        )

        create_a_pre_config_url = self.reverse_product_resource(
            obj, "create-pre-config-list"
        )

        pre_config_entity_relationship_tree_url = self.reverse_product_resource(
            obj, "pre-config-entity-relationship-tree-list"
        )

        repositories_latest_sqcs_url = self.reverse_product_resource(
            obj, "repositories-sqc-latest-values-list",
        )

        repositories_sqc_historical_values_url = self.reverse_product_resource(
            obj, "repositories-sqc-historical-values-list",
        )

        return {
            'create a new repository': create_a_new_repository_url,
            'get current goal': current_goal_url,
            'get compare all goals': compare_goals_url,
            'get current pre-config': current_pre_config_url,
            'get pre-config entity relationship tree': pre_config_entity_relationship_tree_url,
            'get all repositories latest sqcs': repositories_latest_sqcs_url,
            'get all repositories sqc historical values': repositories_sqc_historical_values_url,
            'create a new goal': create_a_new_goal_url,
            'create a new pre-config': create_a_pre_config_url,
        }


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

    def validate(self, attrs):
        """
        Valida se o nome do repositório é único para o produto
        """
        name = attrs["name"]
        product = self.context["view"].get_product()

        qs = Repository.objects.filter(name=name, product=product)

        if qs.exists():
            raise serializers.ValidationError(
                "Repository with this name already exists."
            )

        return attrs

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

        calculate_sqc_url = self.reverse_repository_resource(
            obj, "calculate-sqc-list",
        )

        github_collector_url = self.reverse_repository_resource(
            obj, "github-collector-list",
        )

        sonarqube_collector_url = self.reverse_repository_resource(
            obj, "sonarqube-collector-list",
        )

        return {
            'collect metric': collect_metric_url,
            'calculate measures': calculate_measures_url,
            'calculate subcharacteristics': calculate_subcharacteristics_url,
            'calculate characteristics': calculate_characteristics_url,
            'calculate sqc': calculate_sqc_url,
            'import metrics from github': github_collector_url,
            'import metrics from SonarQube JSON': sonarqube_collector_url,
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

        sqc_historical_values_url = self.reverse_repository_resource(
            obj, "sqc-historical-values-list",
        )

        return {
            'metrics': metrics_historical_values_url,
            'measures': measures_historical_values_url,
            'subcharacteristics': subcharacteristics_historical_values_url,
            'characteristics': characteristics_historical_values_url,
            'sqc': sqc_historical_values_url,
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

        sqc_latest_values_url = self.reverse_repository_resource(
            obj, "latest-calculated-sqc-list",
        )

        return {
            'metrics': metrics_historical_values_url,
            'measures': measures_latest_values_url,
            'subcharacteristics': subcharacteristics_latest_values_url,
            'characteristics': characteristics_latest_values_url,
            'sqc': sqc_latest_values_url,
        }


class RepositorySQCLatestValueSerializer(serializers.ModelSerializer):
    """
    Serialização do último valor coletado de SQC
    """
    current_sqc = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Repository
        fields = (
            "id",
            "url",
            "name",
            "current_sqc"
        )

    def get_current_sqc(self, repository: Repository):
        sqc = repository.calculated_sqcs.first()
        return SQCSerializer(sqc).data if sqc else {}

    def get_url(self, obj):
        """
        Retorna a URL desse produto
        """
        return reverse(
            "product-detail",
            kwargs={
                "pk": obj.id,
                "organization_pk": obj.product.organization.id,
            },
            request=self.context["request"],
        )


class RepositoriesSQCHistorySerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Repository
        fields = (
            "id",
            "url",
            "name",
            "history"
        )

    def get_url(self, obj):
        """
        Retorna a URL desse produto
        """
        return reverse(
            "product-detail",
            kwargs={
                "pk": obj.id,
                "organization_pk": obj.product.organization.id,
            },
            request=self.context["request"],
        )

    def get_history(self, obj: Repository):
        MAX = settings.MAXIMUM_NUMBER_OF_HISTORICAL_RECORDS

        try:
            qs = obj.calculated_sqcs.all().reverse()[:MAX]
            return SQCSerializer(qs, many=True).data
        except SQC.DoesNotExist:
            return None
