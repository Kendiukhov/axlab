import tempfile
import unittest
from pathlib import Path

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import BatteryConfig
from axlab.pipeline.runner import load_results_as_battery, load_run_from_store, run_battery_and_persist
from axlab.store import ArtifactStore


class RunnerReplayTest(unittest.TestCase):
    def _spec(self) -> UniverseSpec:
        return UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [],
                "max_vars": 1,
                "max_term_size": 1,
            }
        )

    def test_rehydrate_results_from_file(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = run_battery_and_persist(
                spec,
                [(x0, x0)],
                tmpdir,
                config=BatteryConfig(max_model_size=1, max_model_candidates=5),
            )
            results = load_results_as_battery(Path(manifest.results_path))
            self.assertEqual(len(results), 1)
            (left, right), battery = results[0]
            self.assertEqual(left.serialize(), "x0")
            self.assertEqual(right.serialize(), "x0")
            self.assertIsNotNone(battery.features)
            self.assertIn("model_found_count", battery.metrics)

    def test_rehydrate_results_from_store(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ArtifactStore(Path(tmpdir) / "store")
            manifest = run_battery_and_persist(
                spec,
                [(x0, x0)],
                Path(tmpdir) / "run",
                config=BatteryConfig(max_model_size=1, max_model_candidates=5),
                store=store,
            )
            loaded_manifest, results = load_run_from_store(store, manifest.run_id)
            self.assertEqual(loaded_manifest.run_id, manifest.run_id)
            self.assertEqual(len(results), 1)

    def test_rehydrate_implication_proof_steps(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2}],
                "max_vars": 2,
                "max_term_size": 3,
            }
        )
        x0 = Term.var("x0")
        x1 = Term.var("x1")
        axiom = (Term.op("f", [x0, x1]), x0)
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = run_battery_and_persist(
                spec,
                [axiom],
                tmpdir,
                config=BatteryConfig(max_model_size=1, max_model_candidates=5),
            )
            results = load_results_as_battery(Path(manifest.results_path))
            _, battery = results[0]
            probe = next(
                item for item in battery.implications if item.theory == "left_projection"
            )
            self.assertEqual(probe.proof_status, "proved")
            self.assertIsNotNone(probe.proof_steps)
            self.assertGreater(len(probe.proof_steps), 0)


if __name__ == "__main__":
    unittest.main()
