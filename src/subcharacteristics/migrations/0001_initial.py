# Generated by Django 4.0.6 on 2022-08-25 22:14

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('measures', '0001_initial'),
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportedSubCharacteristic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('key', models.CharField(max_length=128, unique=True)),
                ('description', models.TextField(blank=True, max_length=512, null=True)),
                ('measures', models.ManyToManyField(blank=True, related_name='related_subcharacteristics', to='measures.supportedmeasure')),
            ],
        ),
        migrations.CreateModel(
            name='CalculatedSubCharacteristic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('repository', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calculated_subcharacteristics', to='organizations.repository')),
                ('subcharacteristic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calculated_subcharacteristics', to='subcharacteristics.supportedsubcharacteristic')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
