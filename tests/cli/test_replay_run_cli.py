import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import BatteryConfig
from axlab.pipeline.runner import run_battery_and_persist
from axlab.store import ArtifactStore


class ReplayRunCliTest(unittest.TestCase):
    def test_cli_replays_store_run(self) -> None:
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
            store_root = Path(tmpdir) / "store"
            store = ArtifactStore(store_root)
            manifest = run_battery_and_persist(
                spec,
                [(x0, x0)],
                Path(tmpdir) / "run",
                config=BatteryConfig(max_model_size=1, max_model_candidates=5),
                store=store,
            )
            output_path = Path(tmpdir) / "replayed.json"
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "axlab.cli.replay_run",
                    "--store",
                    str(store_root),
                    "--run-id",
                    manifest.run_id,
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["manifest"]["run_id"], manifest.run_id)
            self.assertEqual(len(payload["results"]), 1)


if __name__ == "__main__":
    unittest.main()
