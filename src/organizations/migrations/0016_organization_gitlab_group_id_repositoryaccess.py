import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0015_repository_full_names_not_null'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='gitlab_group_id',
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.CreateModel(
            name='RepositoryAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('checked_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('repository', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accesses', to='organizations.repository')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repository_accesses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Repository accesses',
                'unique_together': {('user', 'repository')},
            },
        ),
    ]
