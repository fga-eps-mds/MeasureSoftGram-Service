# Generated by Django 4.0.6 on 2023-11-07 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0002_organization_admin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repository',
            name='key',
            field=models.SlugField(max_length=128),
        ),
    ]