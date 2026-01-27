from __future__ import annotations

import itertools
import time
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from axlab.core.term import Term
from axlab.core.universe_spec import OperationSpec, UniverseSpec
from axlab.engines.model_finder.interface import ModelSearchArtifact, ModelSearchConfig

def _iter_tables(op: OperationSpec, size: int) -> Iterable[Tuple[int, ...]]:
    slots = size if op.arity == 1 else size * size
    return itertools.product(range(size), repeat=slots)


def _fingerprint(
    size: int, operations: Sequence[OperationSpec], tables: Dict[str, Tuple[int, ...]]
) -> str:
    parts = [f"n={size}"]
    for op in operations:
        table = tables[op.name]
        parts.append(f"{op.name}=" + ",".join(str(value) for value in table))
    return ";".join(parts)


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


def _assignments(vars_list: List[str], size: int) -> Iterable[Dict[str, int]]:
    if not vars_list:
        yield {}
        return
    for values in itertools.product(range(size), repeat=len(vars_list)):
        yield dict(zip(vars_list, values))


def _satisfies_equation(
    left: Term, right: Term, vars_list: List[str], tables: Dict[str, Tuple[int, ...]], size: int
) -> bool:
    for env in _assignments(vars_list, size):
        if _evaluate(left, env, tables, size) != _evaluate(right, env, tables, size):
            return False
    return True


def _satisfies_equations(
    equations: Sequence[Tuple[Term, Term]],
    vars_list: List[str],
    tables: Dict[str, Tuple[int, ...]],
    size: int,
) -> bool:
    for left, right in equations:
        if not _satisfies_equation(left, right, vars_list, tables, size):
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
    if must_violate is not None:
        equation_list = equation_list + [must_violate]
    vars_list = _collect_vars(equation_list)
    tables: Dict[str, Tuple[int, ...]] = {}
    candidates = 0
    start = time.monotonic()
    deadline = start + config.max_seconds
    cutoff = False

    def search(op_index: int) -> Optional[str]:
        nonlocal candidates, cutoff
        if time.monotonic() > deadline:
            cutoff = True
            return None
        if op_index >= len(operations):
            candidates += 1
            if candidates > config.max_candidates:
                cutoff = True
                return None
            if not _satisfies_equations(equations, vars_list, tables, size):
                return None
            if must_violate is not None and _satisfies_equation(
                must_violate[0], must_violate[1], vars_list, tables, size
            ):
                return None
            return _fingerprint(size, operations, tables)
        op = operations[op_index]
        for table in _iter_tables(op, size):
            tables[op.name] = tuple(table)
            fingerprint = search(op_index + 1)
            if fingerprint is not None:
                return fingerprint
            if cutoff:
                return None
        return None

    fingerprint = search(0)
    elapsed_seconds = time.monotonic() - start
    if fingerprint is not None:
        return ModelSearchArtifact("found", size, fingerprint, candidates, elapsed_seconds)
    if cutoff:
        status = "timeout"
        if candidates > config.max_candidates:
            status = "cutoff"
        return ModelSearchArtifact(status, size, None, candidates, elapsed_seconds)
    return ModelSearchArtifact("not_found", size, None, candidates, elapsed_seconds)
