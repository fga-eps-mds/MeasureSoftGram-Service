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


main_router = routers.DefaultRouter()

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


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(main_router.urls)),
    path('api/v1/', include(org_router.urls)),
    path('api/v1/', include(prod_router.urls)),
]

if settings.DEBUG:
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
