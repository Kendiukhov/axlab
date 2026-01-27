from __future__ import annotations

from typing import Dict, Tuple

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.core.symmetry import canonicalize_term


def _rename_vars(term: Term, mapping: Dict[str, str]) -> Term:
    if term.kind == "var":
        if term.value not in mapping:
            mapping[term.value] = f"x{len(mapping)}"
        return Term.var(mapping[term.value])
    return Term.op(term.value, [_rename_vars(arg, mapping) for arg in term.args])


def canonicalize_equation(left: Term, right: Term, spec: UniverseSpec) -> Tuple[Term, Term]:
    op_map = spec.op_map()
    left = canonicalize_term(left, op_map)
    right = canonicalize_term(right, op_map)

    mapping: Dict[str, str] = {}
    left = _rename_vars(left, mapping)
    right = _rename_vars(right, mapping)

    left_key = (left.size(), left.serialize())
    right_key = (right.size(), right.serialize())
    if left_key > right_key:
        left, right = right, left
    return left, right
