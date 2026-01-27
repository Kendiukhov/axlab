from __future__ import annotations

import time
from collections import deque
from typing import Iterable, Optional, Sequence, Tuple

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.engines.prover.interface import ProofArtifact, ProofSearchConfig, ProofStep


class RewritingProver:
    def prove(
        self,
        spec: UniverseSpec,
        axioms: Sequence[Tuple[Term, Term]],
        goal: Tuple[Term, Term],
        config: ProofSearchConfig,
    ) -> ProofArtifact:
        del spec
        start = time.monotonic()
        deadline = start + config.max_seconds

        left, right = goal
        if left.serialize() == right.serialize():
            step = ProofStep("reflexivity", left.serialize(), right.serialize())
            return ProofArtifact("proved", time.monotonic() - start, "reflexivity", None, [step])

        rules = []
        for idx, (lhs, rhs) in enumerate(axioms):
            rules.append((f"axiom_{idx}", lhs, rhs))
            rules.append((f"axiom_{idx}_sym", rhs, lhs))
        rules = _order_rules(rules, config.rule_ordering)

        queue = deque([(left, [])])
        seen = {left.serialize()}
        expanded = 0

        while queue:
            if time.monotonic() >= deadline:
                return ProofArtifact("timeout", time.monotonic() - start, None, None, None)
            term, steps = queue.popleft()
            if len(steps) >= config.max_steps:
                continue
            for rule_name, lhs, rhs in rules:
                for rewritten in _rewrite_term(term, lhs, rhs):
                    serialized = rewritten.serialize()
                    if serialized in seen:
                        continue
                    next_steps = steps + [
                        ProofStep(rule_name, term.serialize(), rewritten.serialize())
                    ]
                    if serialized == right.serialize():
                        return ProofArtifact(
                            "proved",
                            time.monotonic() - start,
                            "rewrite",
                            None,
                            next_steps,
                        )
                    seen.add(serialized)
                    queue.append((rewritten, next_steps))
                    expanded += 1
                    if expanded >= config.max_terms:
                        return ProofArtifact(
                            "cutoff", time.monotonic() - start, None, None, None
                        )

        return ProofArtifact("unknown", time.monotonic() - start, None, None, None)


def _order_rules(
    rules: list[tuple[str, Term, Term]], ordering: str
) -> list[tuple[str, Term, Term]]:
    if ordering == "reverse":
        return list(reversed(rules))
    if ordering == "shortest_lhs":
        return sorted(rules, key=lambda entry: entry[1].size())
    if ordering == "longest_lhs":
        return sorted(rules, key=lambda entry: entry[1].size(), reverse=True)
    return rules


def _rewrite_term(term: Term, lhs: Term, rhs: Term) -> Iterable[Term]:
    mapping = _match(lhs, term, {})
    if mapping is not None:
        yield _apply_substitution(rhs, mapping)
    if term.kind == "op":
        for idx, arg in enumerate(term.args):
            for rewritten_arg in _rewrite_term(arg, lhs, rhs):
                new_args = list(term.args)
                new_args[idx] = rewritten_arg
                yield Term.op(term.value, new_args)


def _match(pattern: Term, target: Term, mapping: dict[str, Term]) -> Optional[dict[str, Term]]:
    if pattern.kind == "var":
        existing = mapping.get(pattern.value)
        if existing is None:
            mapping[pattern.value] = target
            return mapping
        if existing.serialize() == target.serialize():
            return mapping
        return None
    if pattern.kind != target.kind or pattern.value != target.value:
        return None
    if len(pattern.args) != len(target.args):
        return None
    for p_arg, t_arg in zip(pattern.args, target.args):
        mapping = _match(p_arg, t_arg, mapping)
        if mapping is None:
            return None
    return mapping


def _apply_substitution(term: Term, mapping: dict[str, Term]) -> Term:
    if term.kind == "var":
        return mapping.get(term.value, term)
    return Term.op(term.value, [_apply_substitution(arg, mapping) for arg in term.args])
