import tempfile
import unittest
from pathlib import Path

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import BatteryConfig
from axlab.pipeline.runner import load_results, load_run_manifest, run_battery_and_persist


class RunnerPersistenceTest(unittest.TestCase):
    def _spec(self) -> UniverseSpec:
        return UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [],
                "max_vars": 1,
                "max_term_size": 1,
            }
        )

    def _axioms(self):
        x0 = Term.var("x0")
        return [(x0, x0), (x0, Term.var("x0"))]

    def test_persists_manifest_and_results(self) -> None:
        spec = self._spec()
        axioms = self._axioms()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = run_battery_and_persist(
                spec, axioms, tmpdir, BatteryConfig(max_model_size=1)
            )
            manifest_path = Path(tmpdir) / "run.json"
            self.assertTrue(manifest_path.exists())
            self.assertTrue(Path(manifest.results_path).exists())

            loaded_manifest = load_run_manifest(manifest_path)
            self.assertEqual(loaded_manifest.run_id, manifest.run_id)
            results = load_results(manifest.results_path)
            self.assertEqual(len(results), len(axioms))
            self.assertEqual(results[0]["axiom"]["left"], axioms[0][0].serialize())

    def test_run_id_is_deterministic(self) -> None:
        spec = self._spec()
        axioms = self._axioms()
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            manifest1 = run_battery_and_persist(
                spec, axioms, tmp1, BatteryConfig(max_model_size=1)
            )
            manifest2 = run_battery_and_persist(
                spec, axioms, tmp2, BatteryConfig(max_model_size=1)
            )
            self.assertEqual(manifest1.run_id, manifest2.run_id)


if __name__ == "__main__":
    unittest.main()
