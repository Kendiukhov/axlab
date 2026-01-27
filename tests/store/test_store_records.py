import tempfile
import unittest

from axlab.store import ArtifactStore, ImplicationRecord, ModelRecord


class StoreRecordsTest(unittest.TestCase):
    def test_record_and_load_related_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ArtifactStore(tmpdir)
            run_id = "run1"
            axiom_id = "axiom1"
            store.record_axiom(run_id, axiom_id, "x0", "x0", "x0=x0")
            store.record_models(
                run_id,
                axiom_id,
                [
                    ModelRecord(
                        run_id=run_id,
                        axiom_id=axiom_id,
                        size=1,
                        status="found",
                        fingerprint="abc",
                        candidates=10,
                        elapsed_seconds=0.1,
                    )
                ],
            )
            store.record_implications(
                run_id,
                axiom_id,
                [
                    ImplicationRecord(
                        run_id=run_id,
                        axiom_id=axiom_id,
                        theory="commutative",
                        status="confirmed",
                        checked_max_size=2,
                        counterexample_size=None,
                        counterexample_fingerprint=None,
                        proof_status="proved",
                        proof_elapsed_seconds=0.2,
                        proof_steps=[{"rule": "axiom", "left": "x0", "right": "x0"}],
                    )
                ],
            )
            store.record_metrics(
                run_id,
                axiom_id,
                {
                    "left_size": 1,
                    "smallest_model_size": None,
                    "trivial_identity": True,
                },
            )
            note = store.add_note(run_id, axiom_id, "Looks degenerate.")

            axiom = store.load_axiom(run_id, axiom_id)
            self.assertIsNotNone(axiom)
            assert axiom is not None
            self.assertEqual(axiom.left_term, "x0")
            self.assertEqual(axiom.symmetry_class, "x0=x0")

            models = store.load_models(run_id, axiom_id)
            self.assertEqual(len(models), 1)
            self.assertEqual(models[0].size, 1)

            implications = store.load_implications(run_id, axiom_id)
            self.assertEqual(len(implications), 1)
            self.assertEqual(implications[0].theory, "commutative")
            self.assertIsNotNone(implications[0].proof_steps)

            metrics = store.load_metrics(run_id, axiom_id)
            self.assertEqual(metrics["left_size"], 1.0)
            self.assertIsNone(metrics["smallest_model_size"])
            self.assertEqual(metrics["trivial_identity"], 1.0)

            notes = store.load_notes(run_id, axiom_id)
            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0].note_id, note.note_id)


if __name__ == "__main__":
    unittest.main()
