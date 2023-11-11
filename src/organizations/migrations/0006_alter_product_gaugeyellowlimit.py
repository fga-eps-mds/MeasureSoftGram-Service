# Generated by Django 4.0.6 on 2023-11-11 17:58

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0005_product_gaugeredlimit_product_gaugeyellowlimit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='gaugeYellowLimit',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.66000000000000003108624468950438313186168670654296875'), max_digits=2),
        ),
    ]
