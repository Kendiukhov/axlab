import unittest

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import BatteryConfig, analyze_axiom


class BatteryMvpTest(unittest.TestCase):
    def test_syntactic_features_and_degeneracy(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2}],
                "max_vars": 2,
                "max_term_size": 3,
            }
        )
        left = Term.op("f", [Term.var("x0"), Term.var("x1")])
        right = Term.var("x0")
        result = analyze_axiom(spec, left, right, BatteryConfig(max_model_size=1))

        self.assertEqual(result.features.left_size, 1)
        self.assertEqual(result.features.right_size, 3)
        self.assertEqual(result.features.total_size, 4)
        self.assertEqual(result.features.var_count, 2)
        self.assertEqual(result.features.max_depth, 2)
        self.assertEqual(result.features.symmetry_class, "x0=f(x0,x1)")

        self.assertFalse(result.degeneracy.trivial_identity)
        self.assertTrue(result.degeneracy.projection_collapse)
        self.assertFalse(result.degeneracy.constant_collapse)

    def test_constant_collapse(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [{"name": "f", "arity": 2}],
                "max_vars": 2,
                "max_term_size": 3,
            }
        )
        left = Term.var("x0")
        right = Term.op("f", [Term.var("x1"), Term.var("x1")])
        result = analyze_axiom(spec, left, right, BatteryConfig(max_model_size=1))
        self.assertTrue(result.degeneracy.constant_collapse)

    def test_model_spectrum(self) -> None:
        spec = UniverseSpec.from_dict(
            {
                "logic": "equational",
                "operations": [],
                "max_vars": 2,
                "max_term_size": 1,
            }
        )
        left = Term.var("x0")
        right = Term.var("x1")
        result = analyze_axiom(spec, left, right, BatteryConfig(max_model_size=2))

        self.assertEqual(result.model_spectrum[0].status, "found")
        self.assertEqual(result.model_spectrum[1].status, "not_found")
        self.assertEqual(result.smallest_model_size, 1)


if __name__ == "__main__":
    unittest.main()
