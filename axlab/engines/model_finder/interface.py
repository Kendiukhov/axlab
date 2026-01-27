from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Sequence, Tuple

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec


@dataclass(frozen=True)
class ModelSearchConfig:
    max_candidates: int = 10_000
    max_seconds: float = 1.0


@dataclass(frozen=True)
class ModelSearchArtifact:
    status: str
    size: int
    fingerprint: Optional[str]
    candidates: int
    elapsed_seconds: float
    max_depth: Optional[int] = None
    partial_seconds: Optional[float] = None


class ModelFinder(Protocol):
    def find_model(
        self,
        spec: UniverseSpec,
        axioms: Sequence[Tuple[Term, Term]],
        size: int,
        config: ModelSearchConfig,
        must_violate: Optional[Tuple[Term, Term]] = None,
    ) -> ModelSearchArtifact:
        ...
