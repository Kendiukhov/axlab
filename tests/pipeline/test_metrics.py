import unittest

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import BatteryConfig, analyze_axiom


class MetricsTest(unittest.TestCase):
    def test_metrics_for_trivial_axiom(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [],
                "max_vars": 1,
                "max_term_size": 1,
            }
        )
        x0 = Term.var("x0")
        result = analyze_axiom(spec, x0, x0, BatteryConfig(max_model_size=2))
        metrics = result.metrics

        self.assertTrue(metrics["trivial_identity"])
        self.assertEqual(metrics["model_found_count"], 2)
        self.assertEqual(metrics["implication_confirmed_count"], 0)
        self.assertIsNone(metrics["implication_confirmed_ratio"])
        self.assertEqual(metrics["syntactic_complexity"], 4)
        self.assertFalse(metrics["nontrivial_model_spectrum"])
        self.assertEqual(metrics["robustness_under_perturbation"], 1.0)
        self.assertEqual(metrics["perturbation_neighbor_count"], 0)
        self.assertIsNone(metrics["perturbation_signature_agreement_ratio"])
        self.assertIsNone(metrics["perturbation_exact_signature_match_ratio"])
        self.assertIsNone(metrics["known_theory_distance"])
        self.assertIsNone(metrics["proof_step_mean"])
        self.assertIsNone(metrics["proof_step_max"])

    def test_perturbation_metrics_for_neighbor(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [],
                "max_vars": 2,
                "max_term_size": 1,
            }
        )
        x0 = Term.var("x0")
        result = analyze_axiom(
            spec,
            x0,
            x0,
            BatteryConfig(
                max_model_size=2,
                max_model_candidates=10,
                perturbation_max_neighbors=4,
                perturbation_max_model_size=2,
            ),
        )
        metrics = result.metrics
        self.assertEqual(metrics["perturbation_neighbor_count"], 1)
        self.assertEqual(metrics["perturbation_exact_signature_match_ratio"], 0.0)
        self.assertEqual(metrics["perturbation_smallest_model_size_match_ratio"], 1.0)
        self.assertEqual(metrics["robustness_under_perturbation"], 0.0)

    def test_novelty_vs_archive_metric(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [],
                "max_vars": 1,
                "max_term_size": 1,
            }
        )
        x0 = Term.var("x0")

        def archive_lookup(symmetry_class: str) -> dict | None:
            if symmetry_class == "x0=x0":
                return {"symmetry_class": symmetry_class}
            return None

        result = analyze_axiom(
            spec,
            x0,
            x0,
            BatteryConfig(max_model_size=1),
            archive_lookup=archive_lookup,
        )
        self.assertEqual(result.metrics["novelty_vs_archive"], 0.0)


if __name__ == "__main__":
    unittest.main()
