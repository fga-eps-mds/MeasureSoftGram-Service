from typing import Union

from django.db import models
from django.utils import timezone


class SupportedMetric(models.Model):
    """
    Métricas suportadas pelo sistema.

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

    # Identificador único da métrica
    key = models.CharField(max_length=128, unique=True)

    metric_type = models.CharField(
        max_length=15,
        choices=SupportedMetricTypes.choices,
        default=SupportedMetricTypes.FLOAT,
    )
    name = models.CharField(max_length=128)
    description = models.TextField(max_length=512, null=True, blank=True)

    def __str__(self):
        return self.key

    def get_latest_metric_value(self) -> Union[float, str, int, bool]:
        """
        Função que recupera o valor mais recente da métrica
        """
        if latest_metric := self.collected_metrics.first():
            return latest_metric.value
        return None

    def get_latest_metric_values(self) -> list:
        """
        Função que recupera os valores mais recentes de uma métrica.

        Observe que aqui, diferentemente de `get_latest_metric_value`
        retornamos uma lista, pois queremos os valores dessa métrica para
        todos os arquivos do projeto.

        Existem algumas medidas que para calcular é preciso da lista de valores
        de uma métrica em todos os arquivos. Como por exemplo a medida
        test_coverage, que precisa da cobertura (metrica coverage) dos
        vários arquivos quem compõe o repositório.
        """
        if latest_metric := self.collected_metrics.first():
            same_day = latest_metric.created_at

            # Remove hours, minutes and seconds
            begin = same_day.replace(hour=0, minute=0, second=0, microsecond=0)
            end = same_day.replace(hour=23, minute=59, second=59, microsecond=0)

            # Métrica de arquivos (inclusive de arquivos vazios)
            metrics_qs = self.collected_metrics.filter(
                qualifier='FIL',
                created_at__gte=begin,
                created_at__lte=end,
            )

            # Métrica do número de linhas
            ncloc_metric = SupportedMetric.objects.get(key='ncloc')

            # Arquivos vazios (sem código relevante)
            qs = ncloc_metric.collected_metrics.filter(
                created_at__gte=begin,
                created_at__lte=end,
                qualifier='FIL',
                value=0,
            ).values_list('path', flat=True)

            empty_files_set = set(qs)

            # Somente os valores dos arquivos que não são vazios
            return [m.value for m in metrics_qs if m.path not in empty_files_set]

        return []


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

    # As métricas do SonarQube geralmente estão associadas a um arquivo ou diretório
    path = models.CharField(
        max_length=255,
        default=None,
        null=True,
        blank=True,
    )

    # Qualifer informar se essa métrica é de arquivo de teste, de diretório etc
    """
    BRC - Sub-projects
    DIR - Directories
    FIL - Files
    TRK - Projects
    UTS - Test Files
    https://python-sonarqube-api.readthedocs.io/en/latest/sonarqube.community.html#sonarqube.community.components.SonarQubeComponents
    """
    qualifier = models.CharField(
        max_length=5,
        default=None,
        null=True,
        blank=True,
    )

    # dynamic key é usado para especificar atributos dinâmicos de métricas genéricas
    dynamic_key = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    repository = models.ForeignKey(
        to='organizations.Repository',
        related_name='calculated_metrics',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return (
            f'Metric: {self.metric}, Value: {self.value}, '
            f'Created at: {self.created_at}'
        )
