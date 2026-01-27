import tempfile
import unittest

from axlab.store import ArtifactStore


class ArtifactStoreTest(unittest.TestCase):
    def test_write_and_read_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ArtifactStore(tmpdir)
            digest = store.write_json("sample", {"a": 1, "b": 2})
            loaded = store.read_json(digest)
            self.assertEqual(loaded, {"a": 1, "b": 2})

    def test_deterministic_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ArtifactStore(tmpdir)
            digest1 = store.write_json("sample", {"b": 2, "a": 1})
            digest2 = store.write_json("sample", {"a": 1, "b": 2})
            self.assertEqual(digest1, digest2)

    def test_run_record_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ArtifactStore(tmpdir)
            manifest = {"run_id": "abc"}
            results = [{"axiom": "x"}]
            manifest_digest = store.write_json("run_manifest", manifest)
            results_digest = store.write_json("run_results", results)
            store.record_run("abc", {"logic": "equational"}, {"max_model_size": 1}, manifest_digest, results_digest)
            run = store.load_run("abc")
            self.assertIsNotNone(run)
            assert run is not None
            self.assertEqual(run.manifest_digest, manifest_digest)
            self.assertEqual(run.results_digest, results_digest)

    def test_lookup_axiom_by_symmetry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ArtifactStore(tmpdir)
            store.record_axiom("run1", "axiom1", "x0", "x0", "x0=x0")
            match = store.lookup_axiom_by_symmetry("x0=x0")
            self.assertIsNotNone(match)
            assert match is not None
            self.assertEqual(match.run_id, "run1")
            self.assertEqual(match.axiom_id, "axiom1")
            self.assertIsNone(store.lookup_axiom_by_symmetry("x0=x1"))


if __name__ == "__main__":
    unittest.main()
