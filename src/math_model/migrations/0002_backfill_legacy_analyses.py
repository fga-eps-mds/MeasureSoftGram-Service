"""Preserva histórico sem inventar vínculos temporais ou uma AQ global."""
from django.db import migrations

LAYERS = (
    ("metrics", "CollectedMetric"),
    ("measures", "CalculatedMeasure"),
    ("subcharacteristics", "CalculatedSubCharacteristic"),
    ("characteristics", "CalculatedCharacteristic"),
    ("tsqmi", "TSQMI"),
)


def backfill(apps, schema_editor):
    alias = schema_editor.connection.alias
    Analysis = apps.get_model("math_model", "QualityAnalysis")
    # A identidade exata da execução não existe nos registros antigos. Apenas
    # igualdade exata de repo, instante e release conhecida permite agrupamento.
    # Não inferimos a release por janela: isso atribuiria certeza a dados antigos.
    identities = {}
    for app, name in LAYERS:
        Model = apps.get_model(app, name)
        for row in Model.objects.using(alias).filter(analysis__isnull=True).order_by("pk").iterator(chunk_size=1000):
            release_id = row.release_id if name == "CalculatedCharacteristic" else None
            key = (row.repository_id, row.created_at, release_id)
            analysis_id = identities.get(key)
            if analysis_id is None:
                analysis = Analysis.objects.using(alias).create(
                    repository_id=row.repository_id, created_at=row.created_at,
                    release_id=release_id, is_partial=True,
                    missing_inputs=["legacy:execution_identity_unverified"],
                )
                analysis_id = identities[key] = analysis.pk
            Model.objects.using(alias).filter(pk=row.pk).update(analysis_id=analysis_id)


class Migration(migrations.Migration):
    dependencies = [
        ("math_model", "0001_initial"),
        ("metrics", "0004_collectedmetric_analysis"),
        ("measures", "0003_calculatedmeasure_analysis"),
        ("subcharacteristics", "0003_calculatedsubcharacteristic_analysis"),
        ("characteristics", "0007_alter_calculatedcharacteristic_unique_together_and_more"),
        ("tsqmi", "0004_tsqmi_analysis"),
    ]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
