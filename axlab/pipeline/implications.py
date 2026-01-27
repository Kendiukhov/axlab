from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.engines.model_finder.interface import ModelSearchArtifact, ModelSearchConfig
from axlab.engines.prover.interface import ProofSearchConfig, ProofStep
from axlab.engines.prover.rewriting import RewritingProver
from axlab.engines.model_finder.naive import find_model_with_constraints


@dataclass(frozen=True)
class ImplicationConfig:
    max_model_size: int = 3
    max_model_candidates: int = 10_000
    max_model_seconds: float = 1.0
    proof_enabled: bool = True
    proof_max_seconds: float = 1.0
    proof_max_steps: int = 4
    proof_max_terms: int = 500
    proof_rule_ordering: str = "given"


@dataclass(frozen=True)
class KnownTheory:
    name: str
    left: Term
    right: Term


@dataclass(frozen=True)
class ImplicationProbe:
    theory: str
    status: str
    checked_max_size: int
    counterexample_size: Optional[int]
    counterexample_fingerprint: Optional[str]
    proof_status: Optional[str] = None
    proof_elapsed_seconds: Optional[float] = None
    proof_steps: Optional[List[ProofStep]] = None


def _first_op_name(spec: UniverseSpec, arity: int) -> Optional[str]:
    for op in spec.operations:
        if op.arity == arity:
            return op.name
    return None


def _binary_theories(op_name: str) -> List[KnownTheory]:
    x0 = Term.var("x0")
    x1 = Term.var("x1")
    x2 = Term.var("x2")
    x3 = Term.var("x3")
    f = lambda *args: Term.op(op_name, list(args))
    return [
        KnownTheory("associative", f(f(x0, x1), x2), f(x0, f(x1, x2))),
        KnownTheory("commutative", f(x0, x1), f(x1, x0)),
        KnownTheory("idempotent", f(x0, x0), x0),
        KnownTheory("left_alternative", f(f(x0, x0), x1), f(x0, f(x0, x1))),
        KnownTheory("right_alternative", f(x0, f(x1, x1)), f(f(x0, x1), x1)),
        KnownTheory("flexible", f(f(x0, x1), x0), f(x0, f(x1, x0))),
        KnownTheory("left_self_distributive", f(x0, f(x1, x2)), f(f(x0, x1), f(x0, x2))),
        KnownTheory("right_self_distributive", f(f(x0, x1), x2), f(f(x0, x2), f(x1, x2))),
        KnownTheory("medial", f(f(x0, x1), f(x2, x3)), f(f(x0, x2), f(x1, x3))),
        KnownTheory("left_projection", f(x0, x1), x0),
        KnownTheory("right_projection", f(x0, x1), x1),
    ]


def _unary_theories(op_name: str) -> List[KnownTheory]:
    x0 = Term.var("x0")
    g = lambda arg: Term.op(op_name, [arg])
    return [
        KnownTheory("idempotent", g(g(x0)), g(x0)),
        KnownTheory("involutive", g(g(x0)), x0),
    ]


def library_for_spec(spec: UniverseSpec) -> List[KnownTheory]:
    theories: List[KnownTheory] = []
    binary = _first_op_name(spec, 2)
    unary = _first_op_name(spec, 1)
    if binary:
        theories.extend(_binary_theories(binary))
    if unary:
        theories.extend(_unary_theories(unary))
    return theories


def run_implication_probes(
    spec: UniverseSpec,
    axiom: Tuple[Term, Term],
    config: ImplicationConfig,
    theories: Optional[Sequence[KnownTheory]] = None,
    model_finder_with_constraints: Callable[
        [UniverseSpec, Sequence[Tuple[Term, Term]], int, ModelSearchConfig, Optional[Tuple[Term, Term]]],
        ModelSearchArtifact,
    ] = find_model_with_constraints,
) -> List[ImplicationProbe]:
    if theories is None:
        theories = library_for_spec(spec)
    probes: List[ImplicationProbe] = []
    search_config = ModelSearchConfig(
        max_candidates=config.max_model_candidates,
        max_seconds=config.max_model_seconds,
    )
    prover = RewritingProver() if config.proof_enabled else None
    proof_config = ProofSearchConfig(
        max_seconds=config.proof_max_seconds,
        max_steps=config.proof_max_steps,
        max_terms=config.proof_max_terms,
        max_model_size=config.max_model_size,
        max_model_candidates=config.max_model_candidates,
        rule_ordering=config.proof_rule_ordering,
    )

    for theory in theories:
        counterexample_size: Optional[int] = None
        counterexample_fingerprint: Optional[str] = None
        cutoff = False
        for size in range(1, config.max_model_size + 1):
            result = model_finder_with_constraints(
                spec,
                [axiom],
                size,
                search_config,
                must_violate=(theory.left, theory.right),
            )
            if result.status == "found":
                counterexample_size = size
                counterexample_fingerprint = result.fingerprint
                break
            if result.status in ("timeout", "cutoff"):
                cutoff = True
        if counterexample_size is not None:
            status = "counterexample"
        elif cutoff:
            status = "inconclusive"
        else:
            status = "confirmed"
        proof_status = None
        proof_elapsed = None
        proof_steps = None
        if status == "confirmed" and prover is not None:
            artifact = prover.prove(spec, [axiom], (theory.left, theory.right), proof_config)
            proof_status = artifact.status
            proof_elapsed = artifact.elapsed_seconds
            proof_steps = artifact.steps
        probes.append(
            ImplicationProbe(
                theory=theory.name,
                status=status,
                checked_max_size=config.max_model_size,
                counterexample_size=counterexample_size,
                counterexample_fingerprint=counterexample_fingerprint,
                proof_status=proof_status,
                proof_elapsed_seconds=proof_elapsed,
                proof_steps=proof_steps,
            )
        )
    return probes
