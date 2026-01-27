import unittest

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.engines.prover.interface import ProofSearchConfig
from axlab.engines.prover.naive import prove


class NaiveProverTest(unittest.TestCase):
    def _spec(self) -> UniverseSpec:
        return UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [],
                "max_vars": 2,
                "max_term_size": 1,
            }
        )

    def test_proved_by_axiom(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        axioms = [(x0, x0)]
        goal = (x0, x0)
        result = prove(spec, axioms, goal, ProofSearchConfig(max_seconds=1.0))
        self.assertEqual(result.status, "proved")
        self.assertEqual(result.counterexample, None)
        self.assertIsNotNone(result.proof)
        self.assertIsNotNone(result.steps)

    def test_disproved_by_counterexample(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        x1 = Term.var("x1")
        axioms = [(x0, x0)]
        goal = (x0, x1)
        result = prove(
            spec, axioms, goal, ProofSearchConfig(max_seconds=1.0, max_model_size=2)
        )
        self.assertEqual(result.status, "disproved")
        self.assertIsNotNone(result.counterexample)

    def test_timeout(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        x1 = Term.var("x1")
        result = prove(
            spec,
            [],
            (x0, x1),
            ProofSearchConfig(max_seconds=0.0, max_model_size=2),
        )
        self.assertEqual(result.status, "timeout")

    def test_unknown_when_no_counterexample_in_bound(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        x1 = Term.var("x1")
        result = prove(
            spec,
            [],
            (x0, x1),
            ProofSearchConfig(max_seconds=1.0, max_model_size=1),
        )
        self.assertEqual(result.status, "unknown")


if __name__ == "__main__":
    unittest.main()
