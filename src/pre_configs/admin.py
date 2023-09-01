from django.contrib import admin

from pre_configs.models import PreConfig


@admin.register(PreConfig)
class PreConfigAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "created_at",
        "product",
    )
    search_fields = ("name",)
    list_filter = ("product",)
