from django.apps import AppConfig


class UtilsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "utils"

    def ready(self):
        # Provisório: remover junto com utils/core_compat.py ao atualizar para msgram-core >= 1.5.5
        from utils import core_compat

        core_compat.apply()
