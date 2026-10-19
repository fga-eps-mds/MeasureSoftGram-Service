import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_session_tokens(apps, schema_editor):
    # Ate aqui a GitHub Action usava o token de sessao; reaproveitar a chave
    # evita quebrar as integracoes ja configuradas no deploy.
    Token = apps.get_model("authtoken", "Token")
    ApiAccessToken = apps.get_model("accounts", "ApiAccessToken")
    ApiAccessToken.objects.bulk_create(
        [ApiAccessToken(key=token.key, user_id=token.user_id) for token in Token.objects.all()],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_customuser_gitlab_access_token"),
        ("authtoken", "0004_alter_tokenproxy_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiAccessToken",
            fields=[
                ("key", models.CharField(max_length=40, primary_key=True, serialize=False, verbose_name="key")),
                ("created", models.DateTimeField(auto_now_add=True, verbose_name="created")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="api_access_token",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.RunPython(copy_session_tokens, migrations.RunPython.noop),
    ]
