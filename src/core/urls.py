from django.urls import path

from core.views import get_mocked_repository

urlpatterns = [
    path('organizations/1/projects/1/', get_mocked_repository)
]
