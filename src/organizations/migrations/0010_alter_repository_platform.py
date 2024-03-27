# Generated by Django 4.0.6 on 2023-12-04 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0009_alter_repository_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repository',
            name='platform',
            field=models.CharField(
                blank=True,
                choices=[
                    ('github', 'GitHub'),
                    ('gitlab', 'GitLab'),
                    ('bitbucket', 'Bitbucket'),
                    ('subversion (SVN)', 'Subversion (SVN)'),
                    ('mercurial', 'Mercurial'),
                    ('aws code commit', 'AWS CodeCommit'),
                    ('azure repos', 'Azure Repos'),
                    ('outros', 'Outros'),
                ],
                max_length=128,
                null=True,
            ),
        ),
    ]
