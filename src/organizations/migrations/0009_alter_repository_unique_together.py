# Generated by Django 4.0.6 on 2023-11-29 18:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0008_alter_repository_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='repository',
            unique_together={('key', 'product')},
        ),
    ]
