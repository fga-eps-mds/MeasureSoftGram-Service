from django.urls import include, path
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from service import views

app_name = 'service'

# tem o prefixo `api/v1/`
system_router = DefaultRouter()

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
router = DefaultRouter()

router.register(
    'history/subcharacteristics',
    views.CalculatedSubCharacteristicHistoryModelViewSet,
    basename='calculated-subcharacteristics-history',
)

router.register(
    'history/characteristics',
    views.CalculatedCharacteristicHistoryModelViewSet,
    basename='calculated-characteristics-history',
)



router.register(
    'subcharacteristics',
    views.LatestCalculatedSubCharacteristicModelViewSet,
    basename='latest-calculated-subcharacteristics',
)

router.register(
    'characteristics',
    views.LatestCalculatedCharacteristicModelViewSet,
    basename='latest-calculated-characteristics',
)

router.register(
    'current/pre-config',
    views.CurrentPreConfigModelViewSet,
    basename='current-pre-config',
)

router.register(
    'current/goal',
    views.CurrentGoalModelViewSet,
    basename='current-goal',
)

router.register(
    'create/goal',
    views.CreateGoalModelViewSet,
    basename='create-goal',
)

router.register(
    'create/pre-config',
    views.CreatePreConfigModelViewSet,
    basename='create-pre-config',
)

router.register(
    'sqc',
    views.SQCModelViewSet,
    basename='sqc-viewset',
)


urlpatterns = [

    path('entity-relationship-tree/', views.entity_relationship_tree),

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
    # path('', include(system_router.urls)),
    # path('', include(router.urls)),
    # path('', include(org_router.urls)),


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
