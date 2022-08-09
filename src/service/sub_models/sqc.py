

from django.db import models
from django.utils import timezone


class SQC(models.Model):
    """
    Classe que abstrai um a nota final do modelo, também conhecida como SQC.
    """
    class Meta:
        ordering = ['-created_at']

    value = models.FloatField()
    created_at = models.DateTimeField(default=timezone.now)
