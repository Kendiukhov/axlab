import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import BatteryConfig
from axlab.pipeline.runner import compute_axiom_id, compute_run_id


class AutoAgentDriverCliTest(unittest.TestCase):
    def test_driver_logs_deterministic_events(self) -> None:
        spec = {
            "version": "v0",
            "logic": "equational",
            "operations": [],
            "max_vars": 1,
            "max_term_size": 1,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            spec_path = tmp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            output_root = tmp_path / "runs"
            store_root = tmp_path / "store"
            log_path = tmp_path / "agent_log.jsonl"
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "axlab.cli.auto_agent_driver",
                    "--spec",
                    str(spec_path),
                    "--output-root",
                    str(output_root),
                    "--store-root",
                    str(store_root),
                    "--log",
                    str(log_path),
                    "--limit",
                    "2",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)

            entries = [
                json.loads(line)
                for line in log_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            events = {entry["event"]: entry for entry in entries}
            for name in ("state", "enumerate", "run", "analyze", "interpret"):
                self.assertIn(name, events)

            state_event = events["state"]
            self.assertEqual(state_event["cycle"], 0)
            state_data = state_event["data"]
            self.assertEqual(state_data["spec"], spec)
            self.assertEqual(state_data["output_root"], str(output_root))
            self.assertEqual(state_data["store_root"], str(store_root))
            self.assertEqual(state_data["run_count"], 0)
            self.assertEqual(state_data["term_count"], 1)
            self.assertEqual(state_data["axiom_count"], 1)

            enumerate_event = events["enumerate"]
            self.assertEqual(enumerate_event["offset"], 0)
            self.assertEqual(enumerate_event["limit"], 2)
            self.assertEqual(enumerate_event["next_offset"], 1)
            self.assertTrue(enumerate_event["complete"])
            self.assertEqual(enumerate_event["axiom_count"], 1)
            self.assertEqual(enumerate_event["axioms"], [{"left": "x0", "right": "x0"}])

            spec_obj = UniverseSpec.from_dict(spec)
            left = Term.parse("x0")
            right = Term.parse("x0")
            expected_run_id = compute_run_id(spec_obj, [(left, right)], BatteryConfig())
            expected_axiom_id = compute_axiom_id(left, right)

            run_event = events["run"]
            self.assertEqual(run_event["run_id"], expected_run_id)
            self.assertEqual(run_event["axiom_count"], 1)
            self.assertEqual(
                run_event["results_path"],
                str(output_root / expected_run_id / "results.jsonl"),
            )
            self.assertEqual(run_event["run_dir"], str(output_root / expected_run_id))

            analyze_event = events["analyze"]
            self.assertEqual(analyze_event["run_id"], expected_run_id)
            self.assertEqual(len(analyze_event["ranking"]), 1)
            self.assertEqual(analyze_event["ranking"][0]["axiom_id"], expected_axiom_id)
            self.assertEqual(
                analyze_event["ranking"][0]["axiom"], {"left": "x0", "right": "x0"}
            )

            interpret_event = events["interpret"]
            self.assertEqual(interpret_event["run_id"], expected_run_id)
            self.assertEqual(interpret_event["axiom_id"], expected_axiom_id)
            self.assertEqual(interpret_event["axiom"], {"left": "x0", "right": "x0"})
            dossier_path = Path(interpret_event["dossier_path"])
            self.assertEqual(
                dossier_path,
                output_root
                / "dossiers"
                / f"dossier-{expected_run_id}-{expected_axiom_id}.json",
            )
            self.assertTrue(dossier_path.exists())

    def test_driver_respects_offset_limit(self) -> None:
        spec = {
            "version": "v0",
            "logic": "equational",
            "operations": [],
            "max_vars": 2,
            "max_term_size": 1,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            spec_path = tmp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            output_root = tmp_path / "runs"
            store_root = tmp_path / "store"
            log_path = tmp_path / "agent_log.jsonl"
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "axlab.cli.auto_agent_driver",
                    "--spec",
                    str(spec_path),
                    "--output-root",
                    str(output_root),
                    "--store-root",
                    str(store_root),
                    "--log",
                    str(log_path),
                    "--offset",
                    "1",
                    "--limit",
                    "2",
                    "--interpret-top",
                    "0",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)

            entries = [
                json.loads(line)
                for line in log_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            events = {entry["event"]: entry for entry in entries}
            enumerate_event = events["enumerate"]
            self.assertEqual(enumerate_event["limit"], 2)
            self.assertEqual(len(enumerate_event["axioms"]), 2)

            run_event = events["run"]
            self.assertEqual(run_event["axiom_count"], 2)

    def test_driver_logs_compare_delta(self) -> None:
        spec = {
            "version": "v0",
            "logic": "equational",
            "operations": [{"name": "f", "arity": 1}],
            "max_vars": 1,
            "max_term_size": 2,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            spec_path = tmp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            output_root = tmp_path / "runs"
            store_root = tmp_path / "store"
            log_path = tmp_path / "agent_log.jsonl"
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "axlab.cli.auto_agent_driver",
                    "--spec",
                    str(spec_path),
                    "--output-root",
                    str(output_root),
                    "--store-root",
                    str(store_root),
                    "--log",
                    str(log_path),
                    "--limit",
                    "2",
                    "--interpret-top",
                    "0",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)

            entries = [
                json.loads(line)
                for line in log_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            enumerate_entries = [entry for entry in entries if entry["event"] == "enumerate"]
            self.assertEqual(len(enumerate_entries), 1)
            self.assertGreaterEqual(enumerate_entries[0]["axiom_count"], 2)

            compare_entries = [entry for entry in entries if entry["event"] == "compare"]
            self.assertEqual(len(compare_entries), 1)
            compare_event = compare_entries[0]
            metrics_a = compare_event["metrics_a"]
            metrics_b = compare_event["metrics_b"]
            expected_delta = {}
            expected_equal = {}
            for key in sorted(set(metrics_a) | set(metrics_b)):
                left = metrics_a.get(key)
                right = metrics_b.get(key)
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    expected_delta[key] = right - left
                    expected_equal[key] = left == right
                else:
                    expected_delta[key] = None
                    expected_equal[key] = left == right
            self.assertEqual(compare_event["delta"], expected_delta)
            self.assertEqual(compare_event["equal"], expected_equal)

if __name__ == "__main__":
    unittest.main()
