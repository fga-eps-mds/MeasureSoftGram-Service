from django.db import models
from django.utils import timezone


class QualityAnalysis(models.Model):
    """
    Representa uma execução completa (ou parcial) do cálculo do modelo matemático
    para um repositório, opcionalmente associada a uma Release ativa.
    """

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["release", "repository", "-created_at", "-id"]),
            models.Index(fields=["repository", "-created_at", "-id"]),
        ]

    repository = models.ForeignKey(
        to="organizations.Repository",
        related_name="quality_analyses",
        on_delete=models.CASCADE,
    )
    release = models.ForeignKey(
        to="releases.Release",
        related_name="quality_analyses",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    release_configuration = models.ForeignKey(
        to="release_configuration.ReleaseConfiguration",
        related_name="quality_analyses",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(default=timezone.now)
    is_partial = models.BooleanField(default=False)
    missing_inputs = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"QualityAnalysis #{self.id} - repo={self.repository_id} release={self.release_id}"
