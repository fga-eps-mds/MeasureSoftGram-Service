from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        # Importa os signals para registrar o receiver save_github_token, que
        # persiste o github_access_token no login social. O import tem efeito
        # colateral (conecta o receiver); o noqa evita que o lint o remova de
        # novo, como aconteceu no commit 283ce41.
        import accounts.signals  # noqa: F401
