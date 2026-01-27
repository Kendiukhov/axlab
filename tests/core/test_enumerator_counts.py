import unittest

from axlab.core.enumerator import enumerate_terms
from axlab.core.universe_spec import UniverseSpec


class EnumeratorCountsTest(unittest.TestCase):
    def test_single_var_commutative_binary(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2, "commutative": True}],
                "max_vars": 1,
                "max_term_size": 3,
            }
        )
        terms = list(enumerate_terms(spec))
        serialized = [term.serialize() for term in terms]
        self.assertEqual(serialized, ["x0", "f(x0,x0)"])

    def test_two_vars_commutative_binary(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2, "commutative": True}],
                "max_vars": 2,
                "max_term_size": 3,
            }
        )
        terms = list(enumerate_terms(spec))
        serialized = [term.serialize() for term in terms]
        self.assertEqual(
            serialized,
            ["x0", "x1", "f(x0,x0)", "f(x0,x1)", "f(x1,x1)"]
        )


if __name__ == "__main__":
    unittest.main()
