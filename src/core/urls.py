from django.urls import path

from core import views

urlpatterns = [
    path('organizations/1/repository/1/', views.get_mocked_repository),
    path('organizations/1/repository/1/measures/', views.get_mocked_measures)
]
