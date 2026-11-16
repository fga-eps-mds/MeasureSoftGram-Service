"""Upgrade de banco populado: preservação de dados e endurecimento das FKs."""

from datetime import timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class LegacyAnalysisMigrationTest(TransactionTestCase):
    def test_upgrade_preserves_every_layer_and_known_release(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        before = {
            "math_model": "0001_initial",
            "metrics": "0004_collectedmetric_analysis",
            "measures": "0003_calculatedmeasure_analysis",
            "subcharacteristics": "0003_calculatedsubcharacteristic_analysis",
            "characteristics": "0007_alter_calculatedcharacteristic_unique_together_and_more",
            "tsqmi": "0004_tsqmi_analysis",
        }
        targets = [(app, before.get(app, name)) for app, name in latest]
        executor.migrate(targets)
        try:
            apps = executor.loader.project_state(targets).apps
            user = apps.get_model("accounts", "CustomUser").objects.create(username="legacy")
            org = apps.get_model("organizations", "Organization").objects.create(name="Legacy")
            product = apps.get_model("organizations", "Product").objects.create(name="Legacy", organization=org)
            repo = apps.get_model("organizations", "Repository").objects.create(name="Legacy", product=product)
            goal = apps.get_model("goals", "Goal").objects.create(product=product, created_by=user, data={})
            at = timezone.now()
            release = apps.get_model("releases", "Release").objects.create(
                product=product,
                created_by=user,
                goal=goal,
                release_name="Legacy",
                start_at=at - timedelta(days=1),
                end_at=at + timedelta(days=1),
            )
            layers = []
            for app, supported, layer, fk in (
                ("metrics", "SupportedMetric", "CollectedMetric", "metric"),
                ("measures", "SupportedMeasure", "CalculatedMeasure", "measure"),
                (
                    "subcharacteristics",
                    "SupportedSubCharacteristic",
                    "CalculatedSubCharacteristic",
                    "subcharacteristic",
                ),
                ("characteristics", "SupportedCharacteristic", "CalculatedCharacteristic", "characteristic"),
            ):
                entity = apps.get_model(app, supported).objects.create(key="legacy", name="Legacy")
                kwargs = {fk: entity, "repository": repo, "value": 0.6, "created_at": at}
                if app == "characteristics":
                    kwargs["release"] = release
                row = apps.get_model(app, layer).objects.create(**kwargs)
                layers.append((app, layer, row.pk))
            row = apps.get_model("tsqmi", "TSQMI").objects.create(repository=repo, value=0.6, created_at=at)
            layers.append(("tsqmi", "TSQMI", row.pk))
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            final = executor.loader.project_state(latest).apps
            for app, name, pk in layers:
                row = final.get_model(app, name).objects.get(pk=pk)
                self.assertEqual(row.value, 0.6)
                self.assertEqual(row.analysis.repository_id, repo.pk)
                self.assertTrue(row.analysis.is_partial)
                self.assertIn("legacy:execution_identity_unverified", row.analysis.missing_inputs)
                self.assertFalse(row._meta.get_field("analysis").null)
                self.assertEqual(row.analysis.release_id, release.pk if app == "characteristics" else None)
        finally:
            MigrationExecutor(connection).migrate(latest)
