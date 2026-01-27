from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

from axlab.core.canonicalization import canonicalize_equation
from axlab.core.perturbation import enumerate_neighbor_axioms
from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.engines.model_finder.interface import ModelSearchConfig
from axlab.engines.model_finder.naive import (
    find_model as find_model_naive,
    find_model_with_constraints as find_model_with_constraints_naive,
)
from axlab.engines.model_finder.prunable import (
    find_model as find_model_prunable,
    find_model_with_constraints as find_model_with_constraints_prunable,
)
from axlab.pipeline.implications import ImplicationConfig, ImplicationProbe, run_implication_probes
from axlab.pipeline.metrics import compute_metrics, compute_novelty_vs_archive


@dataclass(frozen=True)
class BatteryConfig:
    max_model_size: int = 3
    max_model_candidates: int = 10_000
    max_model_seconds: float = 1.0
    model_finder: str = "prunable"
    implication_max_model_size: Optional[int] = None
    implication_max_model_candidates: Optional[int] = None
    implication_max_model_seconds: Optional[float] = None
    perturbation_max_neighbors: int = 8
    perturbation_max_model_size: Optional[int] = None
    perturbation_max_model_candidates: Optional[int] = None
    perturbation_max_model_seconds: Optional[float] = None


@dataclass(frozen=True)
class SyntacticFeatures:
    left_size: int
    right_size: int
    total_size: int
    left_depth: int
    right_depth: int
    max_depth: int
    var_count: int
    symmetry_class: str


@dataclass(frozen=True)
class DegeneracyReport:
    trivial_identity: bool
    projection_collapse: bool
    constant_collapse: bool


@dataclass(frozen=True)
class ModelSpectrumEntry:
    size: int
    status: str
    fingerprint: Optional[str]
    candidates: int
    elapsed_seconds: float


@dataclass(frozen=True)
class PerturbationNeighbor:
    left: Term
    right: Term
    model_statuses: List[str]
    smallest_model_size: Optional[int]


@dataclass(frozen=True)
class BatteryResult:
    features: SyntacticFeatures
    degeneracy: DegeneracyReport
    model_spectrum: List[ModelSpectrumEntry]
    smallest_model_size: Optional[int]
    implications: List[ImplicationProbe]
    perturbation_neighbors: List[PerturbationNeighbor]
    metrics: dict[str, Any]


def _symmetry_class(left: Term, right: Term) -> str:
    return f"{left.serialize()}={right.serialize()}"


def _projection_collapse(left: Term, right: Term) -> bool:
    if left.kind == "op" and right in left.args:
        return True
    if right.kind == "op" and left in right.args:
        return True
    return False


def _constant_collapse(left: Term, right: Term) -> bool:
    if left.kind == "var" and left.value not in set(right.vars()):
        return True
    if right.kind == "var" and right.value not in set(left.vars()):
        return True
    return False


def _neighbor_signature(
    spec: UniverseSpec,
    left: Term,
    right: Term,
    max_size: int,
    search_config: ModelSearchConfig,
    find_model_fn: Callable[[UniverseSpec, Term, Term, int, ModelSearchConfig], Any],
) -> tuple[List[str], Optional[int]]:
    statuses: List[str] = []
    smallest: Optional[int] = None
    for size in range(1, max_size + 1):
        result = find_model_fn(spec, left, right, size, search_config)
        statuses.append(result.status)
        if smallest is None and result.status == "found":
            smallest = size
    return statuses, smallest


def _resolve_model_finder(
    name: str,
) -> Tuple[
    Callable[[UniverseSpec, Term, Term, int, ModelSearchConfig], Any],
    Callable[
        [UniverseSpec, List[Tuple[Term, Term]], int, ModelSearchConfig, Optional[Tuple[Term, Term]]],
        Any,
    ],
]:
    if name == "naive":
        return find_model_naive, find_model_with_constraints_naive
    if name == "prunable":
        return find_model_prunable, find_model_with_constraints_prunable
    raise ValueError(f"Unknown model finder: {name}")


def analyze_axiom(
    spec: UniverseSpec,
    left: Term,
    right: Term,
    config: BatteryConfig | None = None,
    archive_lookup: Optional[Callable[[str], Any]] = None,
) -> BatteryResult:
    if config is None:
        config = BatteryConfig()
    canon_left, canon_right = canonicalize_equation(left, right, spec)
    find_model_fn, find_model_with_constraints_fn = _resolve_model_finder(config.model_finder)

    left_size = canon_left.size()
    right_size = canon_right.size()
    left_depth = canon_left.depth()
    right_depth = canon_right.depth()
    var_count = len(set(canon_left.vars()) | set(canon_right.vars()))
    features = SyntacticFeatures(
        left_size=left_size,
        right_size=right_size,
        total_size=left_size + right_size,
        left_depth=left_depth,
        right_depth=right_depth,
        max_depth=max(left_depth, right_depth),
        var_count=var_count,
        symmetry_class=_symmetry_class(canon_left, canon_right),
    )

    degeneracy = DegeneracyReport(
        trivial_identity=canon_left.serialize() == canon_right.serialize(),
        projection_collapse=_projection_collapse(canon_left, canon_right),
        constant_collapse=_constant_collapse(canon_left, canon_right),
    )

    model_spectrum: List[ModelSpectrumEntry] = []
    smallest_model_size: Optional[int] = None
    search_config = ModelSearchConfig(
        max_candidates=config.max_model_candidates,
        max_seconds=config.max_model_seconds,
    )
    for size in range(1, config.max_model_size + 1):
        result = find_model_fn(spec, canon_left, canon_right, size, search_config)
        model_spectrum.append(
            ModelSpectrumEntry(
                size=size,
                status=result.status,
                fingerprint=result.fingerprint,
                candidates=result.candidates,
                elapsed_seconds=result.elapsed_seconds,
            )
        )
        if smallest_model_size is None and result.status == "found":
            smallest_model_size = size

    implication_config = ImplicationConfig(
        max_model_size=config.implication_max_model_size or config.max_model_size,
        max_model_candidates=config.implication_max_model_candidates or config.max_model_candidates,
        max_model_seconds=config.implication_max_model_seconds or config.max_model_seconds,
    )
    implications = run_implication_probes(
        spec,
        (canon_left, canon_right),
        implication_config,
        model_finder_with_constraints=find_model_with_constraints_fn,
    )

    perturbation_neighbors: List[PerturbationNeighbor] = []
    neighbor_limit = config.perturbation_max_neighbors
    neighbor_max_size = config.perturbation_max_model_size or config.max_model_size
    neighbor_max_size = min(neighbor_max_size, config.max_model_size)
    if neighbor_limit > 0 and neighbor_max_size > 0:
        neighbor_axioms = enumerate_neighbor_axioms(
            spec, canon_left, canon_right, limit=neighbor_limit
        )
        neighbor_search = ModelSearchConfig(
            max_candidates=config.perturbation_max_model_candidates or config.max_model_candidates,
            max_seconds=config.perturbation_max_model_seconds or config.max_model_seconds,
        )
        for n_left, n_right in neighbor_axioms:
            statuses, neighbor_smallest = _neighbor_signature(
                spec, n_left, n_right, neighbor_max_size, neighbor_search, find_model_fn
            )
            perturbation_neighbors.append(
                PerturbationNeighbor(
                    left=n_left,
                    right=n_right,
                    model_statuses=statuses,
                    smallest_model_size=neighbor_smallest,
                )
            )

    novelty_vs_archive = None
    if archive_lookup is not None:
        novelty_vs_archive = compute_novelty_vs_archive(
            features.symmetry_class, archive_lookup
        )

    metrics = compute_metrics(
        features,
        degeneracy,
        model_spectrum,
        implications,
        smallest_model_size,
        novelty_vs_archive=novelty_vs_archive,
        perturbation_neighbors=perturbation_neighbors,
    )

    return BatteryResult(
        features=features,
        degeneracy=degeneracy,
        model_spectrum=model_spectrum,
        smallest_model_size=smallest_model_size,
        implications=implications,
        perturbation_neighbors=perturbation_neighbors,
        metrics=metrics,
    )
