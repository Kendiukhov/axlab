from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from axlab.core.canonicalization import canonicalize_equation
from axlab.core.term import Term
from axlab.core.universe_spec import OperationSpec, UniverseSpec


def _op_choices(spec: UniverseSpec) -> Dict[int, List[OperationSpec]]:
    choices: Dict[int, List[OperationSpec]] = {}
    for op in sorted(spec.operations, key=lambda item: item.name):
        choices.setdefault(op.arity, []).append(op)
    return choices


def enumerate_neighbor_terms(spec: UniverseSpec, term: Term) -> List[Term]:
    var_names = list(spec.variable_names())
    op_map = spec.op_map()
    op_choices = _op_choices(spec)
    neighbors: Dict[str, Term] = {}

    def add(candidate: Term) -> None:
        neighbors.setdefault(candidate.serialize(), candidate)

    def collect(current: Term) -> None:
        if current.kind == "var":
            for name in var_names:
                if name != current.value:
                    add(Term.var(name))
            return
        op_spec = op_map[current.value]
        for op in op_choices.get(len(current.args), []):
            if op.name != current.value:
                add(Term.op(op.name, current.args))
        if len(current.args) == 2 and not op_spec.commutative:
            add(Term.op(current.value, [current.args[1], current.args[0]]))
        for idx, arg in enumerate(current.args):
            for neighbor in enumerate_neighbor_terms(spec, arg):
                new_args = list(current.args)
                new_args[idx] = neighbor
                add(Term.op(current.value, new_args))

    collect(term)
    return [neighbors[key] for key in sorted(neighbors)]


def enumerate_neighbor_axioms(
    spec: UniverseSpec,
    left: Term,
    right: Term,
    limit: int | None = None,
) -> List[Tuple[Term, Term]]:
    canon_left, canon_right = canonicalize_equation(left, right, spec)
    base_key = f"{canon_left.serialize()}={canon_right.serialize()}"
    neighbors: Dict[str, Tuple[Term, Term]] = {}

    for candidate in enumerate_neighbor_terms(spec, canon_left):
        n_left, n_right = canonicalize_equation(candidate, canon_right, spec)
        key = f"{n_left.serialize()}={n_right.serialize()}"
        if key != base_key:
            neighbors.setdefault(key, (n_left, n_right))

    for candidate in enumerate_neighbor_terms(spec, canon_right):
        n_left, n_right = canonicalize_equation(canon_left, candidate, spec)
        key = f"{n_left.serialize()}={n_right.serialize()}"
        if key != base_key:
            neighbors.setdefault(key, (n_left, n_right))

    ordered = [neighbors[key] for key in sorted(neighbors)]
    if limit is not None:
        return ordered[:limit]
    return ordered
