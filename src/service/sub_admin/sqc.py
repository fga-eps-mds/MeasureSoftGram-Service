from django.contrib import admin

from service import models


@admin.register(models.SQC)
class SQCAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "value",
        "created_at",
    )
