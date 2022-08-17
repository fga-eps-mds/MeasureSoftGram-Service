from django.urls import include, path
from rest_framework_nested.routers import DefaultRouter

from service import views

app_name = 'service'

# tem o prefixo `api/v1/`
system_router = DefaultRouter()

system_router.register(
    'supported-metrics',
    views.SupportedMetricModelViewSet,
    basename='supported-metrics',
)

system_router.register(
    'supported-measures',
    views.SupportedMeasureModelViewSet,
    basename='supported-measures',
)

system_router.register(
    'supported-subcharacteristics',
    views.SupportedSubCharacteristicModelViewSet,
    basename='supported-subcharacteristics',
)

system_router.register(
    'supported-characteristics',
    views.SupportedCharacteristicModelViewSet,
    basename='supported-characteristics',
)

# tem o prefixo `api/v1/organizations/<int>/repository/<int>/`
repo_router = DefaultRouter()


repo_router.register(
    'create/metrics',
    views.CollectedMetricModelViewSet,
    basename='collected-metrics',
)

repo_router.register(
    'history/metrics',
    views.CollectedMetricHistoryModelViewSet,
    basename='collected-metrics-history',
)

repo_router.register(
    'history/measures',
    views.CalculatedMeasureHistoryModelViewSet,
    basename='collected-measures-history',
)

repo_router.register(
    'history/subcharacteristics',
    views.CalculatedSubCharacteristicHistoryModelViewSet,
    basename='calculated-subcharacteristics-history',
)

repo_router.register(
    'history/characteristics',
    views.CalculatedCharacteristicHistoryModelViewSet,
    basename='calculated-characteristics-history',
)

repo_router.register(
    'measures',
    views.LatestCalculatedMeasureModelViewSet,
    basename='latest-calculated-measures',
)

repo_router.register(
    'metrics',
    views.LatestCollectedMetricModelViewSet,
    basename='latest-collected-metrics',
)

repo_router.register(
    'subcharacteristics',
    views.LatestCalculatedSubCharacteristicModelViewSet,
    basename='latest-calculated-subcharacteristics',
)

repo_router.register(
    'characteristics',
    views.LatestCalculatedCharacteristicModelViewSet,
    basename='latest-calculated-characteristics',
)

repo_router.register(
    'current/pre-config',
    views.CurrentPreConfigModelViewSet,
    basename='current-pre-config',
)

repo_router.register(
    'current/goal',
    views.CurrentGoalModelViewSet,
    basename='current-goal',
)

repo_router.register(
    'create/goal',
    views.CreateGoalModelViewSet,
    basename='create-goal',
)

repo_router.register(
    'create/pre-config',
    views.CreatePreConfigModelViewSet,
    basename='create-pre-config',
)

repo_router.register(
    'sqc',
    views.SQCModelViewSet,
    basename='sqc-viewset',
)


urlpatterns = [

    path('entity-relationship-tree/', views.entity_relationship_tree),

    path('organizations/1/repository/1/', views.get_mocked_repository),

    path(
        'organizations/1/repository/1/entity-relationship-tree/',
        views.pre_config_entity_relationship_tree,
    ),

    path(
        'organizations/1/repository/1/import/sonarqube-metrics/',
        views.import_sonar_metrics_view
    ),

    path(
        'organizations/1/repository/1/import/github-metrics/',
        views.import_github_metrics,
    ),

    # BEGIN REAL Endpoints
    path('', include(system_router.urls)),

    path('organizations/1/repository/1/', include(repo_router.urls)),

    path(
        'organizations/1/repository/1/calculate/measures/',
        views.calculate_measures,
    ),

    path(
        'organizations/1/repository/1/calculate/subcharacteristics/',
        views.calculate_subcharacteristics,
    ),

    path(
        'organizations/1/repository/1/calculate/characteristics/',
        views.calculate_characteristics,
    ),

    path(
        'organizations/1/repository/1/calculate/sqc/',
        views.calculate_sqc,
    ),

    # END REAL Endpoints
]
