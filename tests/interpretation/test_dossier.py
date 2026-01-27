import re
import tempfile
import unittest
from pathlib import Path

from axlab.api import EnvironmentState, dispatch
from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.interpretation import InterpretationConfig, interpret_axiom
from axlab.pipeline.battery import BatteryConfig, analyze_axiom


class InterpretationToolchainTest(unittest.TestCase):
    def _spec(self) -> UniverseSpec:
        return UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2}],
                "max_vars": 4,
                "max_term_size": 2,
            }
        )

    def test_interpret_axiom_basic(self) -> None:
        spec = self._spec()
        left = Term.parse("f(x0,x0)")
        right = Term.parse("x0")
        config = BatteryConfig(max_model_size=2, max_model_candidates=200, max_model_seconds=0.2)
        result = analyze_axiom(spec, left, right, config)
        dossier = interpret_axiom(
            spec,
            (left, right),
            result,
            InterpretationConfig.from_battery_config(config),
        )
        property_names = {prop.name for prop in dossier.properties}
        self.assertIn("associative", property_names)
        self.assertTrue(dossier.narrative)
        if result.smallest_model_size is not None:
            self.assertEqual(dossier.smallest_model_size, result.smallest_model_size)
        if result.smallest_model_size is not None:
            self.assertTrue(dossier.model_pretty)

    def test_interpret_action_with_neighbors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "runs"
            store_root = Path(tmpdir) / "store"
            state = EnvironmentState.from_spec(
                self._spec(),
                output_root,
                store_root,
                BatteryConfig(max_model_size=1, max_model_candidates=50, max_model_seconds=0.1),
            )
            axioms = [
                {"left": "x0", "right": "x0"},
                {"left": "f(x0,x0)", "right": "x0"},
            ]
            run = dispatch(state, {"action": "run_battery", "payload": {"axioms": axioms}})
            self.assertEqual(run["status"], "ok")
            run_id = run["data"]["run_id"]
            interpret = dispatch(
                state,
                {
                    "action": "interpret",
                    "payload": {"run_id": run_id, "axiom": axioms[0], "config": {"neighbor_count": 1}},
                },
            )
            self.assertEqual(interpret["status"], "ok")
            dossier = interpret["data"]["dossier"]
            self.assertIn("properties", dossier)
            self.assertEqual(len(dossier["nearest_neighbors"]), 1)

    def test_dossier_citations_present(self) -> None:
        spec = self._spec()
        left = Term.parse("f(x0,x0)")
        right = Term.parse("x0")
        config = BatteryConfig(max_model_size=2, max_model_candidates=200, max_model_seconds=0.2)
        result = analyze_axiom(spec, left, right, config)
        dossier = interpret_axiom(
            spec,
            (left, right),
            result,
            InterpretationConfig.from_battery_config(config),
        )
        for fact in dossier.facts:
            self.assertTrue(fact.source)
        for line in dossier.narrative:
            self.assertRegex(line, r"\[[^\]]+\]")


if __name__ == "__main__":
    unittest.main()
