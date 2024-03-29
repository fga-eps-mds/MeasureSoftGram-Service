# Generated by Django 4.0.6 on 2023-12-09 22:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0002_alter_release_table'),
        (
            'organizations',
            '0005_product_gaugeredlimit_product_gaugeyellowlimit',
        ),
        (
            'characteristics',
            '0004_alter_calculatedcharacteristic_unique_together',
        ),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='calculatedcharacteristic',
            unique_together={('repository', 'release', 'characteristic')},
        ),
    ]
