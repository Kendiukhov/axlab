from __future__ import annotations

from typing import Dict

from axlab.core.term import Term
from axlab.core.universe_spec import OperationSpec


def canonicalize_term(term: Term, operations: Dict[str, OperationSpec]) -> Term:
    if term.kind == "var":
        return term
    op = operations[term.value]
    args = tuple(canonicalize_term(arg, operations) for arg in term.args)
    if op.arity == 2 and op.commutative:
        left, right = args
        if left.serialize() > right.serialize():
            args = (right, left)
    return Term.op(term.value, args)
