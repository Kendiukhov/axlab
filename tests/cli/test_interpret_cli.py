import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import BatteryConfig
from axlab.pipeline.runner import run_battery_and_persist


class InterpretCliTest(unittest.TestCase):
    def test_cli_interprets_run_dir(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [],
                "max_vars": 1,
                "max_term_size": 1,
            }
        )
        x0 = Term.var("x0")
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            run_battery_and_persist(
                spec,
                [(x0, x0)],
                run_dir,
                config=BatteryConfig(max_model_size=1, max_model_candidates=5),
            )
            output_path = Path(tmpdir) / "dossier.json"
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "axlab.cli.interpret",
                    "--run-dir",
                    str(run_dir),
                    "--axiom-left",
                    "x0",
                    "--axiom-right",
                    "x0",
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("axiom_id", payload)
            self.assertIn("dossier", payload)
            self.assertEqual(payload["dossier"]["axiom"]["left"], "x0")

    def test_cli_rejects_malformed_dossier(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [],
                "max_vars": 1,
                "max_term_size": 1,
            }
        )
        x0 = Term.var("x0")
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            run_battery_and_persist(
                spec,
                [(x0, x0)],
                run_dir,
                config=BatteryConfig(max_model_size=1, max_model_candidates=5),
            )
            script = dedent(
                f"""
                import sys
                from unittest.mock import patch

                from axlab.cli import interpret as interpret_cli
                from axlab.interpretation.toolchain import Fact, TheoryDossier

                broken = TheoryDossier(
                    axiom={{"left": "x0", "right": "x0"}},
                    canonical_axiom={{"left": "x0", "right": "x0"}},
                    minimal_basis=[{{"left": "x0", "right": "x0"}}],
                    features={{}},
                    degeneracy={{}},
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

                with patch("axlab.cli.interpret.interpret_axiom", return_value=broken):
                    sys.exit(
                        interpret_cli.main(
                            [
                                "--run-dir",
                                "{run_dir}",
                                "--axiom-left",
                                "x0",
                                "--axiom-right",
                                "x0",
                            ]
                        )
                    )
                """
            )
            result = subprocess.run(
                ["python3", "-c", script],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("citation", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
