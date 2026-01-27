import tempfile
import unittest
from pathlib import Path

from axlab.core.universe_spec import OperationSpec, UniverseSpec
from axlab.pipeline.battery import BatteryConfig
from axlab.pipeline.implications import library_for_spec
from axlab.pipeline.runner import load_results_as_battery, run_battery_and_persist


class KnownTheorySanityTest(unittest.TestCase):
    def test_known_theories_confirm_self_identity(self) -> None:
        spec = UniverseSpec(
            version="v0",
            logic="equational",
            operations=[OperationSpec(name="f", arity=2, commutative=False)],
            max_vars=2,
            max_term_size=5,
        )
        theories = library_for_spec(spec)
        axioms = [(theory.left, theory.right) for theory in theories]
        config = BatteryConfig(
            max_model_size=3,
            max_model_candidates=20_000,
            max_model_seconds=1.0,
            implication_max_model_size=3,
            implication_max_model_candidates=50_000,
            implication_max_model_seconds=5.0,
            perturbation_max_neighbors=0,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            run_battery_and_persist(spec, axioms, tmpdir, config)
            results = load_results_as_battery(Path(tmpdir) / "results.jsonl")

        by_axiom = {
            (left.serialize(), right.serialize()): result for (left, right), result in results
        }
        for theory in theories:
            key = (theory.left.serialize(), theory.right.serialize())
            self.assertIn(key, by_axiom)
            result = by_axiom[key]
            probe = next(
                (probe for probe in result.implications if probe.theory == theory.name), None
            )
            self.assertIsNotNone(probe, msg=f"Missing probe for {theory.name}")
            self.assertEqual(
                probe.status,
                "confirmed",
                msg=f"Expected {theory.name} to confirm itself, got {probe.status}",
            )


if __name__ == "__main__":
    unittest.main()
