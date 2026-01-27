import tempfile
import unittest

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import BatteryConfig
from axlab.pipeline.runner import run_battery_and_persist
from axlab.store import ArtifactStore


class RunnerStoreTest(unittest.TestCase):
    def _spec(self) -> UniverseSpec:
        return UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2}],
                "max_vars": 1,
                "max_term_size": 1,
            }
        )

    def test_persists_to_store(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        axioms = [(x0, x0)]
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ArtifactStore(tmpdir)
            manifest = run_battery_and_persist(
                spec, axioms, tmpdir, BatteryConfig(max_model_size=1), store=store
            )
            record = store.load_run(manifest.run_id)
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(store.read_json(record.manifest_digest)["run_id"], manifest.run_id)
            results_payload = store.read_bytes(record.results_digest).decode("utf-8").strip()
            self.assertEqual(len(results_payload.splitlines()), 1)
            axioms = store.list_axioms(manifest.run_id)
            self.assertEqual(len(axioms), 1)
            axiom_id = axioms[0].axiom_id
            models = store.load_models(manifest.run_id, axiom_id)
            self.assertEqual(len(models), 1)
            implications = store.load_implications(manifest.run_id, axiom_id)
            self.assertGreaterEqual(len(implications), 1)
            metrics = store.load_metrics(manifest.run_id, axiom_id)
            self.assertIn("left_size", metrics)
            self.assertIn("model_found_count", metrics)
            self.assertEqual(metrics["novelty_vs_archive"], 1.0)


if __name__ == "__main__":
    unittest.main()
