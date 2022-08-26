from django.urls import path
from rest_framework_nested.routers import DefaultRouter

from service import views

app_name = 'service'


urlpatterns = [
    path('entity-relationship-tree/', views.entity_relationship_tree),

    path(
        'organizations/1/repository/1/entity-relationship-tree/',
        views.pre_config_entity_relationship_tree,
    ),
]
