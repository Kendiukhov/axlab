from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec


def _terms_of_size(spec: UniverseSpec) -> Dict[int, List[Term]]:
    op_map = spec.op_map()
    cache: Dict[int, List[Term]] = {1: [Term.var(name) for name in spec.variable_names()]}

    for size in range(2, spec.max_term_size + 1):
        terms: List[Term] = []
        for op in op_map.values():
            if op.arity == 1:
                for sub in cache.get(size - 1, []):
                    terms.append(Term.op(op.name, [sub]))
            elif op.arity == 2:
                for left_size in range(1, size - 1):
                    right_size = size - 1 - left_size
                    for left in cache.get(left_size, []):
                        for right in cache.get(right_size, []):
                            if op.commutative and left.serialize() > right.serialize():
                                continue
                            terms.append(Term.op(op.name, [left, right]))
        cache[size] = terms
    return cache


def enumerate_terms(spec: UniverseSpec) -> Iterable[Term]:
    cache = _terms_of_size(spec)
    for size in range(1, spec.max_term_size + 1):
        for term in cache.get(size, []):
            yield term


def enumerate_axioms(spec: UniverseSpec) -> Iterable[Tuple[Term, Term]]:
    terms = list(enumerate_terms(spec))
    for left in terms:
        for right in terms:
            yield left, right
