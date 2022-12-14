from django.conf import settings

from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from dj_rest_auth.registration.views import SocialLoginView

from accounts.models import CustomUser
from accounts.serializers import (
    AccountsCreateSerializer, AccountsLoginSerializer,
    AccountsRetrieveSerializer
)


class GithubLoginViewSet(SocialLoginView):
    """
    ViewSet para login via OAuth2 do Github
    """
    adapter_class = GitHubOAuth2Adapter
    callback_url = settings.LOGIN_REDIRECT_URL
    client_class = OAuth2Client


class CreateAccountViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para criação de conta
    """
    queryset = CustomUser.objects.all()
    serializer_class = AccountsCreateSerializer

class RetrieveAccountViewSet(
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para recuperar informações de conta
    """
    permission_classes = (IsAuthenticated,)

    serializer_class = AccountsRetrieveSerializer

    def get_object(self):
        return self.request.user
     
class LoginViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para login de conta
    """
    queryset = CustomUser.objects.all()
    serializer_class = AccountsLoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response({'key': result.key}, status=status.HTTP_200_OK)


class LogoutViewSet(
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para logout de conta
    """
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        self.request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
