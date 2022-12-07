from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework_nested import routers

from characteristics.views import (
    CalculateCharacteristicViewSet,
    CalculatedCharacteristicHistoryModelViewSet,
    LatestCalculatedCharacteristicModelViewSet,
    SupportedCharacteristicModelViewSet,
)
from collectors.github.view import ImportGithubMetricsViewSet
from collectors.sonarqube.view import ImportSonarQubeMetricsViewSet
from entity_trees.views import (
    PreConfigEntitiesRelationshipTreeViewSet,
    SupportedEntitiesRelationshipTreeViewSet,
)
from goals.views import CreateGoalModelViewSet, CurrentGoalModelViewSet
from measures.views import (
    CalculatedMeasureHistoryModelViewSet,
    CalculateMeasuresViewSet,
    LatestCalculatedMeasureModelViewSet,
    SupportedMeasureModelViewSet,
)
from metrics.views import (
    CollectedMetricHistoryModelViewSet,
    CollectedMetricModelViewSet,
    LatestCollectedMetricModelViewSet,
    SupportedMetricModelViewSet,
)
from organizations.views import (
    OrganizationViewSet,
    ProductViewSet,
    RepositoriesSQCHistoryViewSet,
    RepositoriesSQCLatestValueViewSet,
    RepositoryViewSet,
)
from pre_configs.views import CreatePreConfigModelViewSet, CurrentPreConfigModelViewSet
from sqc.views import (
    CalculatedSQCHistoryModelViewSet,
    CalculateSQC,
    LatestCalculatedSQCViewSet,
)
from subcharacteristics.views import (
    CalculatedSubCharacteristicHistoryModelViewSet,
    CalculateSubCharacteristicViewSet,
    LatestCalculatedSubCharacteristicModelViewSet,
    SupportedSubCharacteristicModelViewSet,
)


def register_supported_entities_endpoints(router):
    router.register('supported-metrics', SupportedMetricModelViewSet)
    router.register('supported-measures', SupportedMeasureModelViewSet)
    router.register('supported-subcharacteristics', SupportedSubCharacteristicModelViewSet)
    router.register('supported-characteristics', SupportedCharacteristicModelViewSet)

    router.register(
        'entity-relationship-tree',
        SupportedEntitiesRelationshipTreeViewSet,
        basename='entity-relationship-tree',
    )


def register_repository_actions_endpoints(router):
    router.register(
        'collect/metrics',
        CollectedMetricModelViewSet,
    )

    router.register(
        'calculate/measures',
        CalculateMeasuresViewSet,
        basename='calculate-measures',
    )

    router.register(
        'calculate/subcharacteristics',
        CalculateSubCharacteristicViewSet,
        basename='calculate-subcharacteristics',
    )

    router.register(
        'calculate/characteristics',
        CalculateCharacteristicViewSet,
        basename='calculate-characteristics',
    )

    router.register('calculate/sqc', CalculateSQC, basename='calculate-sqc')


def register_latest_values_endpoints(router):
    router.register(
        'latest-values/metrics',
        LatestCollectedMetricModelViewSet,
        basename='latest-collected-metrics',
    )

    router.register(
        'latest-values/measures',
        LatestCalculatedMeasureModelViewSet,
        basename='latest-calculated-measures',
    )

    router.register(
        'latest-values/subcharacteristics',
        LatestCalculatedSubCharacteristicModelViewSet,
        basename='latest-calculated-subcharacteristics',
    )

    router.register(
        'latest-values/characteristics',
        LatestCalculatedCharacteristicModelViewSet,
        basename='latest-calculated-characteristics',
    )

    router.register(
        'latest-values/sqc',
        LatestCalculatedSQCViewSet,
        basename='latest-calculated-sqc',
    )


def register_historic_values_endpoints(router):
    router.register(
        'historical-values/metrics',
        CollectedMetricHistoryModelViewSet,
        basename='metrics-historical-values',
    )

    router.register(
        'historical-values/measures',
        CalculatedMeasureHistoryModelViewSet,
        basename='measures-historical-values',
    )

    router.register(
        'historical-values/subcharacteristics',
        CalculatedSubCharacteristicHistoryModelViewSet,
        basename='subcharacteristics-historical-values',
    )

    router.register(
        'historical-values/characteristics',
        CalculatedCharacteristicHistoryModelViewSet,
        basename='characteristics-historical-values',
    )

    router.register(
        'historical-values/sqc',
        CalculatedSQCHistoryModelViewSet,
        basename='sqc-historical-values',
    )


def register_collectors_endpoints(router):
    router.register(
        'collectors/github',
        ImportGithubMetricsViewSet,
        basename='github-collector',
    )

    router.register(
        'collectors/sonarqube',
        ImportSonarQubeMetricsViewSet,
        basename='sonarqube-collector',
    )


def register_goals_endpoints(router):
    router.register(
        'current/goal',
        CurrentGoalModelViewSet,
        basename='current-goal',
    )

    router.register(
        'create/goal',
        CreateGoalModelViewSet,
        basename='create-goal',
    )


def register_preconfigs_endpoints(router):
    router.register(
        'current/pre-config',
        CurrentPreConfigModelViewSet,
        basename='current-pre-config',
    )

    router.register(
        'create/pre-config',
        CreatePreConfigModelViewSet,
        basename='create-pre-config',
    )


main_router = routers.DefaultRouter()

register_supported_entities_endpoints(main_router)

main_router.register('organizations', OrganizationViewSet)

org_router = routers.NestedDefaultRouter(
    main_router,
    'organizations',
    lookup='organization',
)

org_router.register('products', ProductViewSet)

prod_router = routers.NestedDefaultRouter(
    org_router,
    'products',
    lookup='product',
)

prod_router.register(
    'entity-relationship-tree',
    PreConfigEntitiesRelationshipTreeViewSet,
    basename='pre-config-entity-relationship-tree',
)

prod_router.register(
    'repositories-sqc-latest-values',
    RepositoriesSQCLatestValueViewSet,
    basename='repositories-sqc-latest-values',
)

prod_router.register(
    'repositories-sqc-historical-values',
    RepositoriesSQCHistoryViewSet,
    basename='repositories-sqc-historical-values',
)

register_goals_endpoints(prod_router)
register_preconfigs_endpoints(prod_router)

prod_router.register('repositories', RepositoryViewSet)

repo_router = routers.NestedDefaultRouter(
    prod_router,
    'repositories',
    lookup='repository',
)

register_repository_actions_endpoints(repo_router)
register_latest_values_endpoints(repo_router)
register_historic_values_endpoints(repo_router)
register_collectors_endpoints(repo_router)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(main_router.urls)),
    path('api/v1/', include(org_router.urls)),
    path('api/v1/', include(prod_router.urls)),
    path('api/v1/', include(repo_router.urls)),
    path('api/v1/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
