import unittest

from axlab.core.canonicalization import canonicalize_equation
from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec


class CanonicalizationTest(unittest.TestCase):
    def test_commutative_op_and_variable_renaming(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2, "commutative": True}],
                "max_vars": 3,
                "max_term_size": 5,
            }
        )
        left = Term.op("f", [Term.var("y"), Term.var("x")])
        right = Term.op("f", [Term.var("z"), Term.var("x")])
        canon_left, canon_right = canonicalize_equation(left, right, spec)
        self.assertEqual(canon_left.serialize(), "f(x0,x1)")
        self.assertEqual(canon_right.serialize(), "f(x0,x2)")

    def test_equation_side_ordering(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "g", "arity": 1}],
                "max_vars": 1,
                "max_term_size": 3,
            }
        )
        left = Term.op("g", [Term.var("x")])
        right = Term.var("x")
        canon_left, canon_right = canonicalize_equation(left, right, spec)
        self.assertEqual(canon_left.serialize(), "x0")
        self.assertEqual(canon_right.serialize(), "g(x0)")


if __name__ == "__main__":
    unittest.main()
