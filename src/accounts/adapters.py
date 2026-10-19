from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.db import transaction

from accounts.signals import save_github_token


class EncryptedTokenSocialAccountAdapter(DefaultSocialAccountAdapter):
    @transaction.atomic
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        # Persist the token on first signup as well as subsequent social logins.
        save_github_token(request, sociallogin)
        return user
