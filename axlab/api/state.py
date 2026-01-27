from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from axlab.core.enumerator import enumerate_terms
from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import BatteryConfig
from axlab.store import ArtifactStore


@dataclass
class EnvironmentState:
    spec: UniverseSpec
    battery_config: BatteryConfig
    output_root: Path
    store: Optional[ArtifactStore]
    run_history: List[str] = field(default_factory=list)
    _terms: List[Term] = field(default_factory=list, repr=False)
    term_count: int = 0
    axiom_count: int = 0

    @classmethod
    def from_spec(
        cls,
        spec: UniverseSpec,
        output_root: str | Path,
        store_root: str | Path | None = None,
        battery_config: BatteryConfig | None = None,
    ) -> "EnvironmentState":
        if battery_config is None:
            battery_config = BatteryConfig()
        output_path = Path(output_root)
        output_path.mkdir(parents=True, exist_ok=True)
        store = ArtifactStore(store_root) if store_root is not None else None
        terms = list(enumerate_terms(spec))
        term_count = len(terms)
        return cls(
            spec=spec,
            battery_config=battery_config,
            output_root=output_path,
            store=store,
            _terms=terms,
            term_count=term_count,
            axiom_count=term_count * term_count,
        )

    def axiom_at(self, index: int) -> Tuple[Term, Term]:
        if index < 0 or index >= self.axiom_count:
            raise IndexError("Axiom index out of range.")
        if self.term_count == 0:
            raise ValueError("UniverseSpec has no terms.")
        left_idx = index // self.term_count
        right_idx = index % self.term_count
        return self._terms[left_idx], self._terms[right_idx]

    def axioms_slice(self, offset: int, limit: int) -> List[Tuple[Term, Term]]:
        if limit < 0:
            raise ValueError("limit must be >= 0.")
        if offset < 0:
            raise ValueError("offset must be >= 0.")
        end = min(self.axiom_count, offset + limit)
        return [self.axiom_at(idx) for idx in range(offset, end)]

    def to_dict(self) -> dict:
        return {
            "spec": self.spec.to_dict(),
            "battery_config": self.battery_config.__dict__,
            "output_root": str(self.output_root),
            "store_root": str(self.store.root) if self.store is not None else None,
            "run_count": len(self.run_history),
            "term_count": self.term_count,
            "axiom_count": self.axiom_count,
        }
