import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from axlab.api import EnvironmentState, dispatch
from axlab.core.universe_spec import UniverseSpec
from axlab.interpretation.toolchain import Fact, TheoryDossier
from axlab.pipeline.battery import BatteryConfig


class ApiActionsTest(unittest.TestCase):
    def _spec(self) -> UniverseSpec:
        return UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2}],
                "max_vars": 1,
                "max_term_size": 1,
            }
        )

    def test_state_and_enumerate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state = EnvironmentState.from_spec(self._spec(), tmpdir)
            response = dispatch(state, {"action": "state"})
            self.assertEqual(response["status"], "ok")
            self.assertEqual(response["data"]["axiom_count"], 1)
            enum = dispatch(state, {"action": "enumerate", "payload": {"limit": 5}})
            self.assertEqual(enum["status"], "ok")
            self.assertEqual(enum["data"]["axioms"], [{"left": "x0", "right": "x0"}])
            self.assertTrue(enum["data"]["complete"])

    def test_run_battery_and_compare_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "runs"
            store_root = Path(tmpdir) / "store"
            state = EnvironmentState.from_spec(
                self._spec(),
                output_root,
                store_root,
                BatteryConfig(max_model_size=1),
            )
            run = dispatch(
                state,
                {
                    "action": "run_battery",
                    "payload": {"axioms": [{"left": "x0", "right": "x0"}]},
                },
            )
            self.assertEqual(run["status"], "ok")
            run_id = run["data"]["run_id"]
            compare = dispatch(
                state,
                {
                    "action": "compare_metrics",
                    "payload": {
                        "run_id": run_id,
                        "axiom_a": {"left": "x0", "right": "x0"},
                        "axiom_b": {"left": "x0", "right": "x0"},
                    },
                },
            )
            self.assertEqual(compare["status"], "ok")
            self.assertIn("left_size", compare["data"]["delta"])
            self.assertEqual(compare["data"]["delta"]["left_size"], 0.0)
            compare_alias = dispatch(
                state,
                {
                    "action": "compare",
                    "payload": {
                        "run_id": run_id,
                        "axiom_a": {"left": "x0", "right": "x0"},
                        "axiom_b": {"left": "x0", "right": "x0"},
                    },
                },
            )
            self.assertEqual(compare_alias["status"], "ok")

    def test_load_run_and_interpret(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "runs"
            store_root = Path(tmpdir) / "store"
            state = EnvironmentState.from_spec(
                self._spec(),
                output_root,
                store_root,
                BatteryConfig(max_model_size=1),
            )
            run = dispatch(
                state,
                {
                    "action": "run",
                    "payload": {"axioms": [{"left": "x0", "right": "x0"}]},
                },
            )
            self.assertEqual(run["status"], "ok")
            run_id = run["data"]["run_id"]

            load_by_id = dispatch(
                state,
                {"action": "load_run", "payload": {"run_id": run_id, "include_results": True}},
            )
            self.assertEqual(load_by_id["status"], "ok")
            self.assertEqual(len(load_by_id["data"]["results"]), 1)

            run_dir = output_root / run_id
            load_by_dir = dispatch(
                state,
                {"action": "load_run", "payload": {"run_dir": str(run_dir)}},
            )
            self.assertEqual(load_by_dir["status"], "ok")
            self.assertEqual(load_by_dir["data"]["manifest"]["run_id"], run_id)

            interpret = dispatch(
                state,
                {
                    "action": "interpret",
                    "payload": {"run_id": run_id, "axiom": {"left": "x0", "right": "x0"}},
                },
            )
            self.assertEqual(interpret["status"], "ok")
            self.assertIn("dossier", interpret["data"])

    def test_interpret_validates_dossier_citations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state = EnvironmentState.from_spec(self._spec(), tmpdir)
            broken = TheoryDossier(
                axiom={"left": "x0", "right": "x0"},
                canonical_axiom={"left": "x0", "right": "x0"},
                minimal_basis=[{"left": "x0", "right": "x0"}],
                features={},
                degeneracy={},
                model_spectrum=[],
                model_pretty=[],
                properties=[],
                benchmark_identities=[],
                derived_laws=[Fact(statement="law", source="")],
                translations=[],
                nearest_neighbors=[],
                facts=[Fact(statement="fact", source="")],
                narrative=["No citations here."],
                open_questions=[],
            )
            with patch("axlab.api.actions.interpret_axiom", return_value=broken):
                interpret = dispatch(
                    state,
                    {"action": "interpret", "payload": {"axiom": {"left": "x0", "right": "x0"}}},
                )
            self.assertEqual(interpret["status"], "error")
            self.assertIn("citation", interpret["error"])


if __name__ == "__main__":
    unittest.main()
