import datetime as dt

from django.contrib import admin

# Do not delete this imports
from service.sub_admin import (
    SupportedMetricAdmin,
    CollectedMetricAdmin,
)



# @admin.register(models.QualityCaracteristic)
# class QualityCaracteristicAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "name",
#         "description",
#     )
#     search_fields = ("name",)


# @admin.register(models.SubQualityCaracteristic)
# class SubQualityCaracteristicAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "name",
#         "description",
#         "quality_caracteristic",
#     )
#     search_fields = (
#         "name",
#     )

#     list_filter = (
#         "quality_caracteristic",
#     )



# @admin.register(models.Measure)
# class MeasureAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "name",
#         "value",
#         "created_at",
#     )


# @admin.register(models.Measurement)
# class MeasurementAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "name",
#         "value",
#         "project",
#     )

#     list_filter = (
#         "project",
#     )

#     search_fields = (
#         "name",
#     )
