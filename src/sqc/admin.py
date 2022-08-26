from django.contrib import admin

from sqc.models import SQC


@admin.register(SQC)
class SQCAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "value",
        "created_at",
    )
    list_filter = (
        "repository",
    )
