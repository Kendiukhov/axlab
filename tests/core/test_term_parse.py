import unittest

from axlab.core.term import Term


class TermParseTest(unittest.TestCase):
    def test_round_trip(self) -> None:
        term = Term.op("f", [Term.var("x0"), Term.op("g", [Term.var("x1")])])
        parsed = Term.parse(term.serialize())
        self.assertEqual(parsed.serialize(), term.serialize())


if __name__ == "__main__":
    unittest.main()
