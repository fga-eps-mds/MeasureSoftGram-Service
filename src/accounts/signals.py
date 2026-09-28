from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver


@receiver(social_account_added)
@receiver(social_account_updated)
def save_github_token(request, sociallogin, **kwargs):
    if sociallogin.account.provider == "github" and sociallogin.token and sociallogin.token.token:
        token = sociallogin.token.token
        user = sociallogin.user
        user.github_access_token = token
        user.save(update_fields=["github_access_token"])
