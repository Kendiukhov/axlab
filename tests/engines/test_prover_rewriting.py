import unittest

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.engines.prover.interface import ProofSearchConfig
from axlab.engines.prover.rewriting import RewritingProver


class RewritingProverTest(unittest.TestCase):
    def _spec(self) -> UniverseSpec:
        return UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [],
                "max_vars": 2,
                "max_term_size": 1,
            }
        )

    def test_rewrite_proves_goal(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        x1 = Term.var("x1")
        axioms = [(x0, x1)]
        goal = (x0, x1)
        prover = RewritingProver()
        result = prover.prove(spec, axioms, goal, ProofSearchConfig(max_steps=1))
        self.assertEqual(result.status, "proved")
        self.assertIsNotNone(result.steps)
        self.assertEqual(result.steps[0].rule, "axiom_0")

    def test_rewrite_with_pattern_matching(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        x1 = Term.var("x1")
        f = lambda a, b: Term.op("f", [a, b])
        axioms = [(f(x0, x1), x0)]
        goal = (f(f(x0, x1), x1), f(x0, x1))
        prover = RewritingProver()
        result = prover.prove(spec, axioms, goal, ProofSearchConfig(max_steps=1))
        self.assertEqual(result.status, "proved")
        self.assertIsNotNone(result.steps)
        self.assertEqual(result.steps[0].rule, "axiom_0")

    def test_rule_ordering_controls_first_match(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        f = lambda a: Term.op("f", [a])
        axioms = [(f(x0), x0), (f(x0), x0)]
        goal = (f(x0), x0)
        prover = RewritingProver()
        result_given = prover.prove(
            spec, axioms, goal, ProofSearchConfig(max_steps=1, rule_ordering="given")
        )
        result_reverse = prover.prove(
            spec, axioms, goal, ProofSearchConfig(max_steps=1, rule_ordering="reverse")
        )
        self.assertIsNotNone(result_given.steps)
        self.assertIsNotNone(result_reverse.steps)
        self.assertEqual(result_given.steps[0].rule, "axiom_0")
        self.assertEqual(result_reverse.steps[0].rule, "axiom_1")

    def test_rewrite_unknown(self) -> None:
        spec = self._spec()
        x0 = Term.var("x0")
        x1 = Term.var("x1")
        prover = RewritingProver()
        result = prover.prove(spec, [], (x0, x1), ProofSearchConfig(max_steps=1))
        self.assertEqual(result.status, "unknown")


if __name__ == "__main__":
    unittest.main()
