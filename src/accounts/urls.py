from django.urls import include, re_path

from accounts.views import GithubLoginViewSet, LogoutViewSet


urlpatterns = [
    re_path(r'^accounts/', include([
        re_path(r'^logout/$', LogoutViewSet.as_view({'delete': 'destroy'}), name='accounts-logout'),
        re_path(r'^github/login/$', GithubLoginViewSet.as_view(), name='github-login')
    ]))
]
