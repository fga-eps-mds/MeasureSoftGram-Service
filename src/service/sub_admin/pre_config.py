from django.contrib import admin

from service import models


@admin.register(models.PreConfig)
class PreConfigAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "created_at",
    )
    search_fields = (
        "name",
    )
    list_filter = (
        "repository",
    )
