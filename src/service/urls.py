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
    'metrics',
    views.LatestCollectedMetricModelViewSet,
    basename='latest-collected-metrics',
)


urlpatterns = [
    # BEGIN MOCKS
    path('organizations/1/repository/1/', views.get_mocked_repository),

    path(
        'organizations/1/repository/1/import/sonarqube-metrics/',
        views.import_sonar_metrics
    ),

    path(
        'organizations/1/repository/1/import/github-metrics/',
        views.import_github_metrics,
    ),

    path(
        'organizations/1/repository/1/measures/',
        views.get_mocked_measures,
    ),

    path(
        'organizations/1/repository/1/measures/<int:measure_id>/',
        views.get_specific_mocked_measure,
    ),

    path(
        'organizations/1/repository/1/history/measures/',
        views.get_mocked_measures_history,
    ),
    # END MOCKS

    # BEGIN REAL Endpoints
    path('', include(system_router.urls)),

    path('organizations/1/repository/1/', include(repo_router.urls)),

    path(
        'organizations/1/repository/1/calculate/measures/<int:measure_id>/',
        views.calculate_measure,
    ),
    # END REAL Endpoints
]
