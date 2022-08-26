from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from rest_framework_nested import routers

from organizations.views import (
    OrganizationViewSet,
    ProductViewSet,
    RepositoryViewSet,
)

from metrics.views import (
    SupportedMetricModelViewSet,
    CollectedMetricModelViewSet,
    LatestCollectedMetricModelViewSet,
    CollectedMetricHistoryModelViewSet,
)

from measures.views import (
    SupportedMeasureModelViewSet,
    CalculateMeasuresViewSet,
    LatestCalculatedMeasureModelViewSet,
    CalculatedMeasureHistoryModelViewSet,
)

from subcharacteristics.views import (
    CalculateSubCharacteristicViewSet,
    CalculatedSubCharacteristicHistoryModelViewSet,
    SupportedSubCharacteristicModelViewSet,
    LatestCalculatedSubCharacteristicModelViewSet,
)

from characteristics.views import (
    CalculateCharacteristicViewSet,
    SupportedCharacteristicModelViewSet,
    LatestCalculatedCharacteristicModelViewSet,
    CalculatedCharacteristicHistoryModelViewSet,
)

from sqc.views import (
    CalculatedSQCHistoryModelViewSet,
    LatestCalculatedSQCViewSet,
    CalculateSQC,
)


def register_supported_entities_endpoints(router):
    router.register('supported-metrics', SupportedMetricModelViewSet)
    router.register('supported-measures', SupportedMeasureModelViewSet)
    router.register('supported-subcharacteristics', SupportedSubCharacteristicModelViewSet)
    router.register('supported-characteristics', SupportedCharacteristicModelViewSet)

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

prod_router.register('repositories', RepositoryViewSet)

repo_router = routers.NestedDefaultRouter(
    prod_router,
    'repositories',
    lookup='repository',
)

register_repository_actions_endpoints(repo_router)
register_latest_values_endpoints(repo_router)
register_historic_values_endpoints(repo_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(main_router.urls)),
    path('api/v1/', include(org_router.urls)),
    path('api/v1/', include(prod_router.urls)),
    path('api/v1/', include(repo_router.urls)),
]

if settings.DEBUG:
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
