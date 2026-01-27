from __future__ import annotations

import time
from typing import Sequence, Tuple

from axlab.core.canonicalization import canonicalize_equation
from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.engines.model_finder.interface import ModelSearchConfig
from axlab.engines.model_finder.naive import find_model_with_constraints
from axlab.engines.prover.interface import ProofArtifact, ProofSearchConfig, ProofStep


_PROOF_AXIOM = "axiom"
_PROOF_REFLEXIVE = "reflexivity"


def _canon_equations(
    spec: UniverseSpec, equations: Sequence[Tuple[Term, Term]]
) -> list[Tuple[Term, Term]]:
    canonical: list[Tuple[Term, Term]] = []
    for left, right in equations:
        canonical.append(canonicalize_equation(left, right, spec))
    return canonical


def _is_reflexive(left: Term, right: Term) -> bool:
    return left.serialize() == right.serialize()


def prove(
    spec: UniverseSpec,
    axioms: Sequence[Tuple[Term, Term]],
    goal: Tuple[Term, Term],
    config: ProofSearchConfig,
) -> ProofArtifact:
    start = time.monotonic()
    deadline = start + config.max_seconds

    canon_axioms = _canon_equations(spec, axioms)
    canon_goal = canonicalize_equation(goal[0], goal[1], spec)

    if _is_reflexive(*canon_goal):
        step = ProofStep(
            rule=_PROOF_REFLEXIVE,
            left=canon_goal[0].serialize(),
            right=canon_goal[1].serialize(),
        )
        return ProofArtifact(
            "proved", time.monotonic() - start, _PROOF_REFLEXIVE, None, [step]
        )
    if canon_goal in canon_axioms:
        step = ProofStep(
            rule=_PROOF_AXIOM,
            left=canon_goal[0].serialize(),
            right=canon_goal[1].serialize(),
        )
        return ProofArtifact("proved", time.monotonic() - start, _PROOF_AXIOM, None, [step])

    for size in range(1, config.max_model_size + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return ProofArtifact("timeout", time.monotonic() - start, None, None, None)
        search_config = ModelSearchConfig(
            max_candidates=config.max_model_candidates,
            max_seconds=remaining,
        )
        result = find_model_with_constraints(
            spec, canon_axioms, size, search_config, must_violate=canon_goal
        )
        if result.status == "found":
            return ProofArtifact(
                "disproved", time.monotonic() - start, None, result.fingerprint, None
            )
        if result.status in {"timeout", "cutoff"}:
            return ProofArtifact("timeout", time.monotonic() - start, None, None, None)

    return ProofArtifact("unknown", time.monotonic() - start, None, None, None)
