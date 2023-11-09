from rest_framework import serializers

from releases.models import Release


class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = (
            "id",
            "release_name",
            "start_at",
            "end_at",
            "created_by",
            "product",
            "goal",
            "description",
        )
