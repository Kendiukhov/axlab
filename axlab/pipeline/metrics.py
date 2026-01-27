from __future__ import annotations

from typing import Any, Callable, Iterable, Optional


def _ratio(numerator: int, denominator: int) -> Optional[float]:
    if denominator <= 0:
        return None
    return numerator / denominator


def _count_status(items: Iterable[Any], attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = getattr(item, attr)
        counts[status] = counts.get(status, 0) + 1
    return counts


def _proof_step_counts(implications: Iterable[Any]) -> list[int]:
    counts: list[int] = []
    for probe in implications:
        if probe.proof_status != "proved":
            continue
        if probe.proof_steps is None:
            continue
        counts.append(len(probe.proof_steps))
    return counts


def _agreement_ratio(base: list[str], candidate: list[str]) -> Optional[float]:
    if not base:
        return None
    matches = sum(1 for left, right in zip(base, candidate) if left == right)
    return matches / len(base)


def compute_novelty_vs_archive(
    symmetry_class: str, archive_lookup: Callable[[str], Any]
) -> float:
    return 0.0 if archive_lookup(symmetry_class) else 1.0


def compute_metrics(
    features: Any,
    degeneracy: Any,
    model_spectrum: list[Any],
    implications: list[Any],
    smallest_model_size: Optional[int],
    novelty_vs_archive: Optional[float] = None,
    perturbation_neighbors: Optional[list[Any]] = None,
) -> dict[str, Any]:
    model_status_counts = _count_status(model_spectrum, "status")
    implication_status_counts = _count_status(implications, "status")

    model_found = model_status_counts.get("found", 0)
    model_not_found = model_status_counts.get("not_found", 0)
    model_timeout = model_status_counts.get("timeout", 0)
    model_cutoff = model_status_counts.get("cutoff", 0)
    model_total = len(model_spectrum)
    model_decisive = model_found + model_not_found

    implication_confirmed = implication_status_counts.get("confirmed", 0)
    implication_counterexample = implication_status_counts.get("counterexample", 0)
    implication_inconclusive = implication_status_counts.get("inconclusive", 0)
    implication_total = len(implications)

    proof_attempted = sum(1 for probe in implications if probe.proof_status is not None)
    proof_proved = sum(1 for probe in implications if probe.proof_status == "proved")
    proof_step_counts = _proof_step_counts(implications)
    proof_step_total = sum(proof_step_counts)
    proof_step_mean = _ratio(proof_step_total, len(proof_step_counts))
    proof_step_max = max(proof_step_counts) if proof_step_counts else None
    known_theory_distance = None
    if implication_total > 0:
        known_theory_distance = (
            implication_counterexample + 0.5 * implication_inconclusive
        ) / implication_total

    perturbation_neighbor_count = 0
    perturbation_signature_agreement_ratio = None
    perturbation_exact_signature_match_ratio = None
    perturbation_smallest_model_size_match_ratio = None
    perturbation_robustness = None
    if perturbation_neighbors:
        perturbation_neighbor_count = len(perturbation_neighbors)
        baseline_statuses = [
            entry.status for entry in model_spectrum[: len(perturbation_neighbors[0].model_statuses)]
        ]
        agreement_ratios: list[float] = []
        exact_matches = 0
        smallest_matches = 0
        for neighbor in perturbation_neighbors:
            ratio = _agreement_ratio(baseline_statuses, neighbor.model_statuses)
            if ratio is not None:
                agreement_ratios.append(ratio)
            if neighbor.model_statuses == baseline_statuses:
                exact_matches += 1
            if neighbor.smallest_model_size == smallest_model_size:
                smallest_matches += 1
        perturbation_signature_agreement_ratio = _ratio(
            sum(agreement_ratios), len(agreement_ratios)
        )
        perturbation_exact_signature_match_ratio = _ratio(
            exact_matches, perturbation_neighbor_count
        )
        perturbation_smallest_model_size_match_ratio = _ratio(
            smallest_matches, perturbation_neighbor_count
        )
        perturbation_robustness = perturbation_exact_signature_match_ratio

    return {
        "left_size": features.left_size,
        "right_size": features.right_size,
        "total_size": features.total_size,
        "left_depth": features.left_depth,
        "right_depth": features.right_depth,
        "max_depth": features.max_depth,
        "var_count": features.var_count,
        "syntactic_complexity": features.total_size + features.max_depth + features.var_count,
        "smallest_model_size": smallest_model_size,
        "trivial_identity": degeneracy.trivial_identity,
        "projection_collapse": degeneracy.projection_collapse,
        "constant_collapse": degeneracy.constant_collapse,
        "nontrivial_model_spectrum": model_found > 0 and model_not_found > 0,
        "model_found_count": model_found,
        "model_not_found_count": model_not_found,
        "model_timeout_count": model_timeout,
        "model_cutoff_count": model_cutoff,
        "model_found_ratio": _ratio(model_found, model_total),
        "model_decisive_ratio": _ratio(model_decisive, model_total),
        "robustness_under_perturbation": perturbation_robustness
        if perturbation_neighbors
        else _ratio(model_decisive, model_total),
        "perturbation_neighbor_count": perturbation_neighbor_count,
        "perturbation_signature_agreement_ratio": perturbation_signature_agreement_ratio,
        "perturbation_exact_signature_match_ratio": perturbation_exact_signature_match_ratio,
        "perturbation_smallest_model_size_match_ratio": perturbation_smallest_model_size_match_ratio,
        "model_candidate_total": sum(entry.candidates for entry in model_spectrum),
        "model_elapsed_total": sum(entry.elapsed_seconds for entry in model_spectrum),
        "implication_confirmed_count": implication_confirmed,
        "implication_counterexample_count": implication_counterexample,
        "implication_inconclusive_count": implication_inconclusive,
        "implication_confirmed_ratio": _ratio(implication_confirmed, implication_total),
        "implication_counterexample_ratio": _ratio(
            implication_counterexample, implication_total
        ),
        "implication_inconclusive_ratio": _ratio(
            implication_inconclusive, implication_total
        ),
        "implication_proof_attempted_count": proof_attempted,
        "implication_proved_count": proof_proved,
        "implication_proved_ratio": _ratio(proof_proved, proof_attempted),
        "proof_step_total": proof_step_total,
        "proof_step_mean": proof_step_mean,
        "proof_step_max": proof_step_max,
        "known_theory_distance": known_theory_distance,
        "novelty_vs_archive": novelty_vs_archive,
    }
