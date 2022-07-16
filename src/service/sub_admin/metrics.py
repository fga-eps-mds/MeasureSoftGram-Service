import datetime as dt

from django.contrib import admin

from service import models


@admin.register(models.SupportedMetric)
class SupportedMetricAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "key",
        "name",
        "metric_type",
        "description",
    )
    search_fields = (
        "key",
        "name",
    )
    list_filter = (
        "metric_type",
    )


@admin.register(models.CollectedMetric)
class CollectedMetricAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_metric_key",
        "get_metric_name",
        "get_value",
        "created_at",
    )
    search_fields = (
        "metric__key",
    )
    list_filter = (
        "metric__metric_type",
    )

    def get_metric_name(self, obj: models.CollectedMetric):
        return obj.metric.name
    get_metric_name.short_description = "Metric name"
    get_metric_name.admin_order_field = "metric__name"

    def get_metric_key(self, obj: models.CollectedMetric):
        return obj.metric.key
    get_metric_key.short_description = "Metric key"
    get_metric_key.admin_order_field = "metric__key"

    def get_value(self, obj: models.CollectedMetric):
        value = obj.value

        MILLISEC = models.SupportedMetric.SupportedMetricTypes.MILLISEC
        if obj.metric.metric_type == MILLISEC:
            value = dt.datetime.fromtimestamp(value)

        return value
    get_value.short_description = "Value"
    get_value.admin_order_field = "value"
