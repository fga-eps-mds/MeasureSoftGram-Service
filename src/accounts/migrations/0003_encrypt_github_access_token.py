from django.db import migrations, models

from accounts.fields import EncryptedTokenField, encrypt_token, token_cipher


def encrypt_existing_tokens(apps, schema_editor):
    User = apps.get_model("accounts", "CustomUser")
    SocialToken = apps.get_model("socialaccount", "SocialToken")
    alias = schema_editor.connection.alias
    users = User.objects.using(alias)
    social_tokens = SocialToken.objects.using(alias).filter(account__provider="github")

    # Validate before changing any rows, including on an empty database.
    token_cipher()
    for user in users.all().iterator(chunk_size=500):
        value = user.github_access_token
        if not value:
            legacy = social_tokens.filter(account__user_id=user.pk).order_by("-pk").first()
            if legacy:
                value = legacy.token
        if value:
            users.filter(pk=user.pk).update(github_access_token=encrypt_token(value))

    # Do not leave a second, plaintext copy in django-allauth's token table.
    social_tokens.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_customuser_github_access_token"),
        ("socialaccount", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="github_access_token",
            field=models.TextField(blank=True, null=True),
        ),
        # Intentionally irreversible: rollback must not silently restore plaintext.
        migrations.RunPython(encrypt_existing_tokens),
        migrations.AlterField(
            model_name="customuser",
            name="github_access_token",
            field=EncryptedTokenField(blank=True, null=True, editable=False),
        ),
    ]
