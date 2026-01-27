from __future__ import annotations

import itertools
import time
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from axlab.core.term import Term
from axlab.core.universe_spec import OperationSpec, UniverseSpec
from axlab.engines.model_finder.interface import ModelSearchArtifact, ModelSearchConfig


def _iter_slots(op: OperationSpec, size: int) -> Iterable[int]:
    slots = size if op.arity == 1 else size * size
    return range(slots)


def _fingerprint(
    size: int, operations: Sequence[OperationSpec], tables: Dict[str, Tuple[int, ...]]
) -> str:
    parts = [f"n={size}"]
    for op in operations:
        table = tables[op.name]
        parts.append(f"{op.name}=" + ",".join(str(value) for value in table))
    return ";".join(parts)


def _assignments(
    vars_list: List[str], size: int
) -> List[Tuple[Dict[str, int], Tuple[int, ...]]]:
    if not vars_list:
        return [({}, ())]
    assignments: List[Tuple[Dict[str, int], Tuple[int, ...]]] = []
    for values in itertools.product(range(size), repeat=len(vars_list)):
        assignments.append((dict(zip(vars_list, values)), values))
    return assignments


def _partial_evaluate(
    term: Term,
    env: Dict[str, int],
    tables: Dict[str, List[Optional[int]]],
    size: int,
    cache: Dict[Tuple[Term, Tuple[int, ...]], Optional[int]],
    env_key: Tuple[int, ...],
) -> Optional[int]:
    key = (term, env_key)
    if key in cache:
        return cache[key]
    if term.kind == "var":
        value = env[term.value]
        cache[key] = value
        return value
    table = tables[term.value]
    if len(term.args) == 1:
        arg = _partial_evaluate(term.args[0], env, tables, size, cache, env_key)
        if arg is None:
            cache[key] = None
            return None
        value = table[arg]
        cache[key] = value
        return value
    left = _partial_evaluate(term.args[0], env, tables, size, cache, env_key)
    if left is None:
        cache[key] = None
        return None
    right = _partial_evaluate(term.args[1], env, tables, size, cache, env_key)
    if right is None:
        cache[key] = None
        return None
    value = table[left * size + right]
    cache[key] = value
    return value


def _partial_consistent(
    equations: Sequence[Tuple[Term, Term]],
    assignments: Sequence[Tuple[Dict[str, int], Tuple[int, ...]]],
    tables: Dict[str, List[Optional[int]]],
    size: int,
) -> bool:
    if not equations:
        return True
    cache: Dict[Tuple[Term, Tuple[int, ...]], Optional[int]] = {}
    for env, env_key in assignments:
        for left, right in equations:
            left_val = _partial_evaluate(left, env, tables, size, cache, env_key)
            right_val = _partial_evaluate(right, env, tables, size, cache, env_key)
            if left_val is not None and right_val is not None and left_val != right_val:
                return False
    return True


def _evaluate(
    term: Term, env: Dict[str, int], tables: Dict[str, Tuple[int, ...]], size: int
) -> int:
    if term.kind == "var":
        return env[term.value]
    table = tables[term.value]
    if len(term.args) == 1:
        return table[_evaluate(term.args[0], env, tables, size)]
    left = _evaluate(term.args[0], env, tables, size)
    right = _evaluate(term.args[1], env, tables, size)
    return table[left * size + right]


def _satisfies_equation(
    left: Term,
    right: Term,
    assignments: Sequence[Tuple[Dict[str, int], Tuple[int, ...]]],
    tables: Dict[str, Tuple[int, ...]],
    size: int,
) -> bool:
    for env, _ in assignments:
        if _evaluate(left, env, tables, size) != _evaluate(right, env, tables, size):
            return False
    return True


def _satisfies_equations(
    equations: Sequence[Tuple[Term, Term]],
    assignments: Sequence[Tuple[Dict[str, int], Tuple[int, ...]]],
    tables: Dict[str, Tuple[int, ...]],
    size: int,
) -> bool:
    for left, right in equations:
        if not _satisfies_equation(left, right, assignments, tables, size):
            return False
    return True


def _collect_vars(equations: Sequence[Tuple[Term, Term]]) -> List[str]:
    names: set[str] = set()
    for left, right in equations:
        names.update(left.vars())
        names.update(right.vars())
    return sorted(names)


def find_model(
    spec: UniverseSpec, left: Term, right: Term, size: int, config: ModelSearchConfig
) -> ModelSearchArtifact:
    return find_model_with_constraints(spec, [(left, right)], size, config)


def find_model_with_constraints(
    spec: UniverseSpec,
    equations: Sequence[Tuple[Term, Term]],
    size: int,
    config: ModelSearchConfig,
    must_violate: Optional[Tuple[Term, Term]] = None,
) -> ModelSearchArtifact:
    operations = list(spec.operations)
    equation_list = list(equations)
    vars_equations = equation_list
    if must_violate is not None:
        vars_equations = vars_equations + [must_violate]
    vars_list = _collect_vars(vars_equations)
    assignments = _assignments(vars_list, size)
    tables: Dict[str, List[Optional[int]]] = {}
    slots: List[Tuple[str, int]] = []
    for op in operations:
        table = [None] * (size if op.arity == 1 else size * size)
        tables[op.name] = table
        for slot in _iter_slots(op, size):
            slots.append((op.name, slot))

    candidates = 0
    start = time.monotonic()
    deadline = start + config.max_seconds
    cutoff = False
    max_depth = 0
    partial_seconds = 0.0

    def materialize_tables() -> Dict[str, Tuple[int, ...]]:
        return {name: tuple(value for value in table) for name, table in tables.items()}

    def search(slot_index: int) -> Optional[str]:
        nonlocal candidates, cutoff, max_depth, partial_seconds
        if slot_index > max_depth:
            max_depth = slot_index
        if time.monotonic() > deadline:
            cutoff = True
            return None
        if slot_index >= len(slots):
            candidates += 1
            if candidates > config.max_candidates:
                cutoff = True
                return None
            full_tables = materialize_tables()
            if not _satisfies_equations(equations, assignments, full_tables, size):
                return None
            if must_violate is not None and _satisfies_equation(
                must_violate[0], must_violate[1], assignments, full_tables, size
            ):
                return None
            return _fingerprint(size, operations, full_tables)
        op_name, slot = slots[slot_index]
        for value in range(size):
            tables[op_name][slot] = value
            partial_start = time.monotonic()
            consistent = _partial_consistent(equations, assignments, tables, size)
            partial_seconds += time.monotonic() - partial_start
            if consistent:
                fingerprint = search(slot_index + 1)
                if fingerprint is not None:
                    return fingerprint
            tables[op_name][slot] = None
            if cutoff:
                return None
        return None

    fingerprint = search(0)
    elapsed_seconds = time.monotonic() - start
    if fingerprint is not None:
        return ModelSearchArtifact(
            "found",
            size,
            fingerprint,
            candidates,
            elapsed_seconds,
            max_depth=max_depth,
            partial_seconds=partial_seconds,
        )
    if cutoff:
        status = "timeout"
        if candidates > config.max_candidates:
            status = "cutoff"
        return ModelSearchArtifact(
            status,
            size,
            None,
            candidates,
            elapsed_seconds,
            max_depth=max_depth,
            partial_seconds=partial_seconds,
        )
    return ModelSearchArtifact(
        "not_found",
        size,
        None,
        candidates,
        elapsed_seconds,
        max_depth=max_depth,
        partial_seconds=partial_seconds,
    )
