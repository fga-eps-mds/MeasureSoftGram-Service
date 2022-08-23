from django.contrib import admin

from service import models


@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
    )
    search_fields = (
        "name",
    )


@admin.register(models.Product)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
    )
    search_fields = (
        "name",
    )
    list_filter = (
        "organization",
    )


@admin.register(models.Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
    )
    search_fields = (
        "name",
    )
    list_filter = (
        "product",
    )
