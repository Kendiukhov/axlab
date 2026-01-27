import json
import tempfile
import unittest
from pathlib import Path

from axlab.api import EnvironmentState, dispatch
from axlab.core.universe_spec import UniverseSpec


class RunDirRelativeResultsApiTest(unittest.TestCase):
    def test_replay_run_with_repo_relative_results(self) -> None:
        fixture_dir = Path(__file__).resolve().parents[1] / "regression" / "fixtures" / "minimal_run"
        run_dir = fixture_dir / "run"
        manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        spec = UniverseSpec.from_dict(manifest["spec"])
        with tempfile.TemporaryDirectory() as tmpdir:
            state = EnvironmentState.from_spec(spec, tmpdir)
            response = dispatch(state, {"action": "replay_run", "payload": {"run_dir": str(run_dir)}})
        self.assertEqual(response["status"], "ok")
        payload = response["data"]
        self.assertEqual(payload["manifest"]["run_id"], manifest["run_id"])
        self.assertEqual(len(payload["results"]), 1)

    def test_interpret_with_repo_relative_results(self) -> None:
        fixture_dir = Path(__file__).resolve().parents[1] / "regression" / "fixtures" / "minimal_run"
        run_dir = fixture_dir / "run"
        manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        spec = UniverseSpec.from_dict(manifest["spec"])
        with tempfile.TemporaryDirectory() as tmpdir:
            state = EnvironmentState.from_spec(spec, tmpdir)
            response = dispatch(
                state,
                {
                    "action": "interpret",
                    "payload": {
                        "run_dir": str(run_dir),
                        "axiom": {"left": "x0", "right": "x0"},
                    },
                },
            )
        self.assertEqual(response["status"], "ok")
        payload = response["data"]
        self.assertEqual(payload["run_id"], manifest["run_id"])
        self.assertEqual(payload["dossier"]["axiom"]["left"], "x0")


if __name__ == "__main__":
    unittest.main()
