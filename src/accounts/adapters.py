from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponseBadRequest

from accounts.signals import save_github_token

EMAIL_ALREADY_REGISTERED = "O e-mail desta conta do {provider} já está em uso por outro usuário do MeasureSoftGram."


class EncryptedTokenSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Sem isso o allauth redireciona para o formulario de signup dele, que
        # nao esta montado nesta API, e o login responde 500.
        if not sociallogin.is_existing and self._email_is_taken(sociallogin):
            provider = sociallogin.account.get_provider().name
            raise ImmediateHttpResponse(HttpResponseBadRequest(EMAIL_ALREADY_REGISTERED.format(provider=provider)))

    @staticmethod
    def _email_is_taken(sociallogin):
        emails = {address.email for address in sociallogin.email_addresses}
        emails.add(sociallogin.user.email)
        emails.discard("")
        return any(get_user_model().objects.filter(email__iexact=email).exists() for email in emails)

    @transaction.atomic
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        # Persist the token on first signup as well as subsequent social logins.
        save_github_token(request, sociallogin)
        return user
