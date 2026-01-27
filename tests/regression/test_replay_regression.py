import json
import unittest
from pathlib import Path

from axlab.pipeline.runner import load_run_from_store, serialize_battery_results
from axlab.store import ArtifactStore


class ReplayRegressionTest(unittest.TestCase):
    def test_replay_minimal_run_matches_golden(self) -> None:
        fixture_dir = Path(__file__).resolve().parent / "fixtures" / "minimal_run"
        golden = json.loads((fixture_dir / "golden.json").read_text(encoding="utf-8"))
        store = ArtifactStore(fixture_dir / "store")
        manifest, results = load_run_from_store(store, golden["manifest"]["run_id"])
        payload = {
            "manifest": manifest.__dict__,
            "results": serialize_battery_results(results),
        }
        self.assertEqual(payload, golden)

    def test_novelty_archive_persists_across_runs(self) -> None:
        fixture_dir = Path(__file__).resolve().parent / "fixtures" / "novelty_archive"
        golden = json.loads((fixture_dir / "golden.json").read_text(encoding="utf-8"))
        store = ArtifactStore(fixture_dir / "store")
        manifest, results = load_run_from_store(store, golden["manifest"]["run_id"])
        payload = {
            "manifest": manifest.__dict__,
            "results": serialize_battery_results(results),
        }
        self.assertEqual(payload, golden)
        novelty = payload["results"][0]["metrics"]["novelty_vs_archive"]
        self.assertEqual(novelty, 0.0)


if __name__ == "__main__":
    unittest.main()
