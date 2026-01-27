import unittest

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.implications import ImplicationConfig, run_implication_probes


class ImplicationProbeTest(unittest.TestCase):
    def test_detects_counterexample(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2}],
                "max_vars": 3,
                "max_term_size": 3,
            }
        )
        x0 = Term.var("x0")
        x1 = Term.var("x1")
        axiom = (Term.op("f", [x0, x1]), Term.op("f", [x1, x0]))
        probes = run_implication_probes(spec, axiom, ImplicationConfig(max_model_size=2))
        assoc = next(probe for probe in probes if probe.theory == "associative")
        self.assertEqual(assoc.status, "counterexample")
        self.assertIsNotNone(assoc.counterexample_size)

    def test_confirms_projection_implies_idempotent(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2}],
                "max_vars": 2,
                "max_term_size": 3,
            }
        )
        x0 = Term.var("x0")
        x1 = Term.var("x1")
        axiom = (Term.op("f", [x0, x1]), x0)
        probes = run_implication_probes(spec, axiom, ImplicationConfig(max_model_size=2))
        idem = next(probe for probe in probes if probe.theory == "idempotent")
        self.assertEqual(idem.status, "confirmed")


if __name__ == "__main__":
    unittest.main()
