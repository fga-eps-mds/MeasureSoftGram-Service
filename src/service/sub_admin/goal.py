from django.contrib import admin

from service import models


@admin.register(models.Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'release_name',
        'start_at',
        'end_at',
    )
    search_fields = (
        "release_name",
    )
