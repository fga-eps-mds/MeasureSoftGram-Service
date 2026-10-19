from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

from accounts.models import ApiAccessToken


class SessionOrApiTokenAuthentication(TokenAuthentication):
    """
    Aceita no header `Authorization: Token <key>` tanto o token de sessão
    (apagado no logout) quanto o token das integrações (ApiAccessToken).
    """

    def authenticate_credentials(self, key):
        api_token = ApiAccessToken.objects.select_related("user").filter(key=key).first()
        if api_token is None:
            return super().authenticate_credentials(key)

        if not api_token.user.is_active:
            raise exceptions.AuthenticationFailed(_("User inactive or deleted."))

        return (api_token.user, api_token)
