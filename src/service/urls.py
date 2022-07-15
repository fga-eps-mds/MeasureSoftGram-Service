from django.urls import include, path
from rest_framework_nested.routers import DefaultRouter

from service import views

app_name = 'service'

router = DefaultRouter()

router.register('metrics', views.MetricModelView, basename='metric')
router.register('measures', views.MeasureModelView, basename='measure')

urlpatterns = [
    path('organizations/1/repository/1/', views.get_mocked_repository),
    path('organizations/1/repository/1/import-sonar-metrics/', views.import_sonar_metrics),
    # path('organizations/1/repository/1/measures/', views.get_mocked_measures),
    path('organizations/1/repository/1/', include(router.urls))
]
