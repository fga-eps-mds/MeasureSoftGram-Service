from django.contrib import admin

from core import models


@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
        "created_at",
        "updated_at",
    )
    search_fields = ("name",)


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'description',
        'github_url',
        'created_at',
        'updated_at',
        'organization',
    )

    search_fields = (
        "name",
    )

    list_filter = (
        'organization',
    )


@admin.register(models.QualityCaracteristic)
class QualityCaracteristicAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
    )
    search_fields = ("name",)


@admin.register(models.SubQualityCaracteristic)
class SubQualityCaracteristicAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
        "quality_caracteristic",
    )
    search_fields = (
        "name",
    )

    list_filter = (
        "quality_caracteristic",
    )


@admin.register(models.Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "subquality_caracteristic",
    )


@admin.register(models.Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "value",
        "project",
    )

    list_filter = (
        "project",
    )

    search_fields = (
        "name",
    )
