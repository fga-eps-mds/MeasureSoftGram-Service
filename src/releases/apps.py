from django.apps import AppConfig


class ReleasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'releases'

    def ready(self):
        from . import jobs

        jobs.check_the_need_to_calculate_releases()
