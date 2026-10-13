from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver


@receiver(social_account_added)
@receiver(social_account_updated)
def save_social_token(request, sociallogin, **kwargs):
    if not (sociallogin and getattr(sociallogin, "token", None) and getattr(sociallogin.token, "token", None)):
        return

    provider = getattr(getattr(sociallogin, "account", None), "provider", None)
    user = getattr(sociallogin, "user", None)
    if not user:
        return

    token = sociallogin.token.token
    if provider == "github":
        user.github_access_token = token
        user.save(update_fields=["github_access_token"])
    elif provider == "gitlab":
        user.gitlab_access_token = token
        user.save(update_fields=["gitlab_access_token"])


# Alias for backwards compatibility with existing imports and adapter
save_github_token = save_social_token
