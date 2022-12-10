from django.urls import include, re_path

from accounts.views import (
    GithubLoginViewSet, LogoutViewSet,
    CreateAccountViewSet, LoginViewSet
)


urlpatterns = [
    re_path(r'^accounts/', include([
        re_path(r'^signin/$', CreateAccountViewSet.as_view({'post': 'create'}), name='accounts-signin'),
        re_path(r'^login/$', LoginViewSet.as_view({'post': 'create'}), name='accounts-login'),
        re_path(r'^logout/$', LogoutViewSet.as_view({'delete': 'destroy'}), name='accounts-logout'),
        re_path(r'^github/login/$', GithubLoginViewSet.as_view(), name='github-login')
    ]))
]
