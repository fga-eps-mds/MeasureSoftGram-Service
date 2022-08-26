from django.contrib import admin

from goals.models import Goal


@admin.register(Goal)
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
    list_filter = (
        "product",
    )
