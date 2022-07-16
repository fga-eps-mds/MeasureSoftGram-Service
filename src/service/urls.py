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
    views.CollectedMetricModelView,
    basename='collected-metrics',
)

urlpatterns = [
    # BEGIN MOCKS
    path('organizations/1/repository/1/', views.get_mocked_repository),

    path(
        'organizations/1/repository/1/import-sonar-metrics/',
        views.import_sonar_metrics
    ),

    path('organizations/1/repository/1/measures/', views.get_mocked_measures),
    # END MOCKS

    # BEGIN REAL Endpoints
    path('', include(system_router.urls)),

    path('organizations/1/repository/1/', include(repo_router.urls)),
    # END REAL Endpoints
]
