# Generated by Django 4.0.6 on 2023-06-30 02:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tsqmi', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tsqmi',
            options={'ordering': ['-created_at'], 'verbose_name': 'TSQMI', 'verbose_name_plural': 'TSQMI'},
        ),
    ]