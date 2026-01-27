from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Sequence, Tuple

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec


@dataclass(frozen=True)
class ProofSearchConfig:
    max_seconds: float = 1.0
    max_model_size: int = 3
    max_model_candidates: int = 10_000
    max_steps: int = 4
    max_terms: int = 500
    rule_ordering: str = "given"


@dataclass(frozen=True)
class ProofStep:
    rule: str
    left: str
    right: str


@dataclass(frozen=True)
class ProofArtifact:
    status: str
    elapsed_seconds: float
    proof: Optional[str]
    counterexample: Optional[str]
    steps: Optional[List[ProofStep]]


class Prover(Protocol):
    def prove(
        self,
        spec: UniverseSpec,
        axioms: Sequence[Tuple[Term, Term]],
        goal: Tuple[Term, Term],
        config: ProofSearchConfig,
    ) -> ProofArtifact:
        ...
