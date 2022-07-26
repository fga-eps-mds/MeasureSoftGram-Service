from django.db import models
from django.utils import timezone


class SupportedMetric(models.Model):
    """
    Métricas suportadas pelo sistema atualmente.

    Somente é possível cadastrar o valor de uma métrica se
    ela estiver cadastrada nesta tabela.
    """
    class Meta:
        ordering = ["key"]

    class SupportedMetricTypes(models.TextChoices):
        INT = ('INT', 'Integer')
        FLOAT = ('FLOAT', 'Float')
        PERCENT = ('PERCENT', 'Percent')
        BOOL = ('BOOL', 'Boolean')
        STRING = ('STRING', 'String')
        DATA = ('DATA', 'Data')
        LEVEL = ('LEVEL', 'Level')
        MILLISEC = ('MILLISEC', 'Milliseconds')
        WORK_DUR = ('WORK_DUR', 'Work Duration')
        DISTRIB = ('DISTRIB', 'Distribution')
        RATING = ('RATING', 'Rating')

    key = models.CharField(max_length=128, unique=True)
    metric_type = models.CharField(
        max_length=15,
        choices=SupportedMetricTypes.choices,
    )
    name = models.CharField(max_length=128)
    description = models.TextField(max_length=512, null=True, blank=True)

    def __str__(self):
        return self.key

    def get_latest_metric_value(self):
        """
        Função que recupera o valor mais recente da métrica
        """
        if latest_metric := self.collected_metrics.first():
            return latest_metric.value
        return None


class CollectedMetric(models.Model):
    """
    Métricas é o maior grau de granualidade de dados.
    São os dados coletados de diversas fontes (SonarQube, GitHub, etc).

    O MeasureSoftGram permite a coleta de qualquer métrica. Desse modo, quando
    é perguntado o valor atual ou histórico das métricas de um projeto, além
    das métricas coletadas pelos usuários, também é retornado o valor das
    métricas famosas, e caso as métricas famosas não tenham sido coletadas, o
    valor da métrica é retornado como None.
    """
    class Meta:
        # Aqui estamos ordenando na ordem decrescente, ou seja, nos querysets
        # os registros mais recentes vem primeiro (qs.first() == mais recente)
        ordering = ['-created_at']

    metric = models.ForeignKey(
        SupportedMetric,
        related_name='collected_metrics',
        on_delete=models.CASCADE,
    )
    value = models.FloatField()
    path = models.CharField(
        max_length=255,
        default=None,
        null=True,
        blank=True,
    )
    qualifier = models.CharField(
        max_length=5,
        default=None,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return (
            f'Metric: {self.metric}, Value: {self.value}, '
            f'Created at: {self.created_at}'
        )
