# Generated by Django 4.0.6 on 2023-07-06 23:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("characteristics", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BalanceMatrix",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "relation_type",
                    models.CharField(
                        choices=[("+", "Positive"), ("-", "Negative")], max_length=1
                    ),
                ),
                (
                    "source_characteristic",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="source_characteristic",
                        to="characteristics.supportedcharacteristic",
                    ),
                ),
                (
                    "target_characteristic",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="target_characteristic",
                        to="characteristics.supportedcharacteristic",
                    ),
                ),
            ],
            options={
                "unique_together": {("source_characteristic", "target_characteristic")},
            },
        ),
    ]