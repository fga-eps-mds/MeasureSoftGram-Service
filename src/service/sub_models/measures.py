from django.db import models
from django.utils import timezone


class SupportedMeasure(models.Model):
    """
    Medidas suportadas pelo sistema atualmente.
    """
    key = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(max_length=512, null=True, blank=True)


class CalculatedMeasure(models.Model):
    """
    Medidas calculadas pelo sistema.
    """
    class Meta:
        # Ordernar na ordem decrescente de criação do registro
        ordering = ['-created_at']

    measure = models.ForeignKey(
        SupportedMeasure,
        related_name='calculated_measures',
        on_delete=models.CASCADE,
    )
    value = models.FloatField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return (
            f'Measure: {self.measure}, Value: {self.value}, '
            f'Created at: {self.created_at}'
        )
