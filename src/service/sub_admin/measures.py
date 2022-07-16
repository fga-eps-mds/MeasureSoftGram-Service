from django.contrib import admin

from service import models


@admin.register(models.SupportedMeasure)
class SupportedMeasureAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "key",
        "name",
        "description",
    )
    search_fields = (
        "key",
        "name",
    )


@admin.register(models.CalculatedMeasure)
class CalculatedMeasureAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_measure_key",
        "get_measure_name",
        "value",
        "created_at",
    )
    search_fields = (
        "measure__key",
        "measure__name",
    )
    list_filter = (
        "measure__name",
    )

    def get_measure_name(self, obj):
        return obj.measure.name
    get_measure_name.short_description = "Measure name"
    get_measure_name.admin_order_field = "measure__name"


    def get_measure_key(self, obj):
        return obj.measure.key
    get_measure_key.short_description = "Measure key"
    get_measure_key.admin_order_field = "measure__key"
