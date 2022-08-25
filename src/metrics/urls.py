from rest_framework_nested.routers import DefaultRouter

from metrics.views import (
    SupportedMetricModelViewSet,
    CollectedMetricModelViewSet,
    LatestCollectedMetricModelViewSet,
    CollectedMetricHistoryModelViewSet,
)

app_name = 'metrics'


metrics_router = DefaultRouter()

metrics_router.register(
    r'supported-metrics',
    SupportedMetricModelViewSet,
    basename='supported-metrics',
)



