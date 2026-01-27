import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class RunDirRelativeResultsTest(unittest.TestCase):
    def test_replay_run_with_repo_relative_results(self) -> None:
        fixture_dir = Path(__file__).resolve().parent / "fixtures" / "minimal_run"
        run_dir = fixture_dir / "run"
        manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "replay.json"
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "axlab.cli.replay_run",
                    "--run-dir",
                    str(run_dir),
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["manifest"]["run_id"], manifest["run_id"])
            self.assertEqual(len(payload["results"]), 1)

    def test_interpret_with_repo_relative_results(self) -> None:
        fixture_dir = Path(__file__).resolve().parent / "fixtures" / "minimal_run"
        run_dir = fixture_dir / "run"
        manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmpdir:
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
            self.assertEqual(payload["run_id"], manifest["run_id"])
            self.assertEqual(payload["dossier"]["axiom"]["left"], "x0")


if __name__ == "__main__":
    unittest.main()
