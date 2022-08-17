from rest_framework import serializers

from service import models


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Goal
        fields = (
            'id',
            'release_name',
            'start_at',
            'end_at',
            'data',
        )
