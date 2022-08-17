from typing import Dict

from django.db import models
from django.utils import timezone


class Goal(models.Model):

    class Meta:
        ordering = ('-created_at',)

    created_at = models.DateTimeField(default=timezone.now)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    release_name = models.CharField(max_length=255)
    data = models.JSONField()

    @staticmethod
    def validate_goal(goal_dict: Dict[str, int]):
        return True

    def save(self, *args, **kwargs):
        if self.id:
            raise ValueError("It's not allowed to update a goal")

        self.validate_goal(self.data)
        return super().save(*args, **kwargs)
