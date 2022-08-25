from cgitb import lookup
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from rest_framework_nested import routers

# import service.urls as ser_urls
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


main_router = routers.DefaultRouter()

main_router.register('organizations', OrganizationViewSet)
main_router.register('supported-metrics', SupportedMetricModelViewSet)


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

repo_router.register(
    'collect/metrics',
    CollectedMetricModelViewSet,
)

repo_router.register(
    'latest-values/metrics',
    LatestCollectedMetricModelViewSet,
    basename='latest-collected-metrics',
)

repo_router.register(
    'historical-values/metrics',
    CollectedMetricHistoryModelViewSet,
    basename='metrics-historical-values',
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(main_router.urls)),
    path('api/v1/', include(org_router.urls)),
    path('api/v1/', include(prod_router.urls)),
    path('api/v1/', include(repo_router.urls)),
]

if settings.DEBUG:
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
