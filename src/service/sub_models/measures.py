from django.db import models
from django.utils import timezone


class SuporteMeasure(models.Model):
    """
    Medidas suportadas pelo sistema atualmente.
    """
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
        SuporteMeasure,
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
