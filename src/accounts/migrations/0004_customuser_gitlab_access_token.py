from django.db import migrations
from accounts.fields import EncryptedTokenField


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_encrypt_github_access_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="gitlab_access_token",
            field=EncryptedTokenField(blank=True, editable=False, null=True),
        ),
    ]

