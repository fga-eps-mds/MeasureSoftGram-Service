from django.db import models
from django.utils import timezone


class SupportedMeasure(models.Model):
    """
    Tabela que lista as medidas suportadas.

    Essa tabela gera uma tabela NxM com a tabela SupportedMetrics. Por meio
    dessa tabela NxM que temos a associação de quais métricas são usadas para
    calcular uma medida
    """
    key = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(
        max_length=512,
        null=True,
        blank=True,
    )

    # Métricas que estão associadas no cálculo dessa medida
    metrics = models.ManyToManyField(
        'SupportedMetric',
        related_name='related_measures',
        blank=True,
    )

    def __str__(self):
        return self.name

    def get_latest_metric_params(self):
        """
        Função que recupera os valores mais recentes das
        métricas que essa medida depende para ser calculada

        TODO: - Melhorar a query para o banco de dados.
              - Desconfio que aqui esteja rolando vários inner joins

        """
        metric_params = {}
        for supported_metric in self.metrics.all():
            key = supported_metric.key
            metric_params[key] = supported_metric.get_latest_metric_value()
        return metric_params


class CalculatedMeasure(models.Model):
    """
    Tabela que armazena todas os valores das medidas já calculadas
    """
    class Meta:
        # Aqui estamos ordenando na ordem decrescente, ou seja, nos querysets os registros mais recentes vem primeiro (qs.first() == mais recente)
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
