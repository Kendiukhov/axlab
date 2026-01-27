from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import (
    BatteryConfig,
    BatteryResult,
    DegeneracyReport,
    ModelSpectrumEntry,
    PerturbationNeighbor,
    SyntacticFeatures,
    analyze_axiom,
)
from axlab.engines.prover.interface import ProofStep
from axlab.pipeline.implications import ImplicationProbe
from axlab.pipeline.metrics import compute_metrics
from axlab.store import ArtifactStore, ImplicationRecord, ModelRecord, RunRecord


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    spec: dict
    battery_config: dict
    axiom_count: int
    results_path: str


def _stable_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _run_id(spec: UniverseSpec, axioms: Iterable[Tuple[Term, Term]], config: BatteryConfig) -> str:
    payload = {
        "spec": spec.to_dict(),
        "battery_config": config.__dict__,
        "axioms": [
            {"left": left.serialize(), "right": right.serialize()} for left, right in axioms
        ],
    }
    digest = hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()
    return digest[:16]


def _axiom_id(left: Term, right: Term) -> str:
    payload = {"left": left.serialize(), "right": right.serialize()}
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def compute_run_id(
    spec: UniverseSpec, axioms: Iterable[Tuple[Term, Term]], config: BatteryConfig
) -> str:
    return _run_id(spec, axioms, config)


def compute_axiom_id(left: Term, right: Term) -> str:
    return _axiom_id(left, right)


def _features_to_dict(result: BatteryResult, metrics_override: dict | None = None) -> dict:
    return {
        "features": result.features.__dict__,
        "degeneracy": result.degeneracy.__dict__,
        "model_spectrum": [entry.__dict__ for entry in result.model_spectrum],
        "smallest_model_size": result.smallest_model_size,
        "implications": [_implication_to_dict(probe) for probe in result.implications],
        "perturbation_neighbors": [
            _perturbation_neighbor_to_dict(neighbor) for neighbor in result.perturbation_neighbors
        ],
        "metrics": metrics_override or result.metrics,
    }


def _implication_to_dict(probe: ImplicationProbe) -> dict:
    data = {
        "theory": probe.theory,
        "status": probe.status,
        "checked_max_size": probe.checked_max_size,
        "counterexample_size": probe.counterexample_size,
        "counterexample_fingerprint": probe.counterexample_fingerprint,
        "proof_status": probe.proof_status,
        "proof_elapsed_seconds": probe.proof_elapsed_seconds,
        "proof_steps": None,
    }
    if probe.proof_steps is not None:
        data["proof_steps"] = [
            {"rule": step.rule, "left": step.left, "right": step.right}
            for step in probe.proof_steps
        ]
    return data


def _perturbation_neighbor_to_dict(neighbor: PerturbationNeighbor) -> dict:
    return {
        "left": neighbor.left.serialize(),
        "right": neighbor.right.serialize(),
        "model_statuses": list(neighbor.model_statuses),
        "smallest_model_size": neighbor.smallest_model_size,
    }


def serialize_battery_results(
    results: List[Tuple[Tuple[Term, Term], BatteryResult]]
) -> List[dict]:
    serialized: List[dict] = []
    for (left, right), result in results:
        serialized.append(
            {
                "axiom": {"left": left.serialize(), "right": right.serialize()},
                **_features_to_dict(result),
            }
        )
    return serialized


def run_battery_and_persist(
    spec: UniverseSpec,
    axioms: Iterable[Tuple[Term, Term]],
    output_dir: str | Path,
    config: BatteryConfig | None = None,
    store: ArtifactStore | None = None,
) -> RunManifest:
    if config is None:
        config = BatteryConfig()
    axiom_list = list(axioms)
    run_id = _run_id(spec, axiom_list, config)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    results_path = output_path / "results.jsonl"

    archive_lookup = None
    if store is not None:
        archive_lookup = store.lookup_axiom_by_symmetry
    with results_path.open("w", encoding="utf-8") as handle:
        for left, right in axiom_list:
            result = analyze_axiom(spec, left, right, config, archive_lookup=archive_lookup)
            metrics = result.metrics
            payload = {
                "axiom": {"left": left.serialize(), "right": right.serialize()},
                **_features_to_dict(result, metrics),
            }
            handle.write(_stable_json(payload))
            handle.write("\n")
            if store is not None:
                axiom_id = _axiom_id(left, right)
                store.record_axiom(
                    run_id,
                    axiom_id,
                    left.serialize(),
                    right.serialize(),
                    result.features.symmetry_class,
                )
                store.record_metrics(run_id, axiom_id, metrics)
                models = [
                    ModelRecord(
                        run_id=run_id,
                        axiom_id=axiom_id,
                        size=entry.size,
                        status=entry.status,
                        fingerprint=entry.fingerprint,
                        candidates=entry.candidates,
                        elapsed_seconds=entry.elapsed_seconds,
                    )
                    for entry in result.model_spectrum
                ]
                store.record_models(run_id, axiom_id, models)
                implications = [
                    ImplicationRecord(
                        run_id=run_id,
                        axiom_id=axiom_id,
                        theory=probe.theory,
                        status=probe.status,
                        checked_max_size=probe.checked_max_size,
                        counterexample_size=probe.counterexample_size,
                        counterexample_fingerprint=probe.counterexample_fingerprint,
                        proof_status=probe.proof_status,
                        proof_elapsed_seconds=probe.proof_elapsed_seconds,
                        proof_steps=[
                            {"rule": step.rule, "left": step.left, "right": step.right}
                            for step in probe.proof_steps
                        ]
                        if probe.proof_steps is not None
                        else None,
                    )
                    for probe in result.implications
                ]
                store.record_implications(run_id, axiom_id, implications)

    manifest = RunManifest(
        run_id=run_id,
        spec=spec.to_dict(),
        battery_config=config.__dict__,
        axiom_count=len(axiom_list),
        results_path=str(results_path),
    )
    manifest_path = output_path / "run.json"
    manifest_path.write_text(_stable_json(manifest.__dict__) + "\n", encoding="utf-8")
    if store is not None:
        manifest_digest = store.write_bytes("run_manifest", manifest_path.read_bytes())
        results_digest = store.write_bytes("run_results", results_path.read_bytes())
        store.record_run(run_id, spec.to_dict(), config.__dict__, manifest_digest, results_digest)
    return manifest


def load_run_manifest(path: str | Path) -> RunManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return RunManifest(
        run_id=data["run_id"],
        spec=data["spec"],
        battery_config=data["battery_config"],
        axiom_count=data["axiom_count"],
        results_path=data["results_path"],
    )


def resolve_results_path(results_path: str | Path, run_dir: str | Path | None = None) -> Path:
    path = Path(results_path)
    if path.is_absolute():
        return path
    if run_dir is None:
        return path
    candidate = Path(run_dir) / path
    if candidate.exists():
        return candidate
    if path.exists():
        return path
    return candidate


def load_results(path: str | Path) -> List[dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return _parse_results_jsonl(handle.read())


def load_results_as_battery(
    path: str | Path,
) -> List[Tuple[Tuple[Term, Term], BatteryResult]]:
    return _rehydrate_results(load_results(path))


def load_run_from_store(
    store: ArtifactStore, run_id: str
) -> Tuple[RunManifest, List[Tuple[Tuple[Term, Term], BatteryResult]]]:
    record = store.load_run(run_id)
    if record is None:
        raise ValueError(f"Unknown run_id: {run_id}")
    manifest = _manifest_from_store(record, store)
    results = _rehydrate_results(_load_results_from_store(record, store))
    return manifest, results


def _load_results_from_store(record: RunRecord, store: ArtifactStore) -> List[dict]:
    payload = store.read_bytes(record.results_digest).decode("utf-8")
    return _parse_results_jsonl(payload)


def _manifest_from_store(record: RunRecord, store: ArtifactStore) -> RunManifest:
    data = store.read_json(record.manifest_digest)
    return RunManifest(
        run_id=data["run_id"],
        spec=data["spec"],
        battery_config=data["battery_config"],
        axiom_count=data["axiom_count"],
        results_path=data["results_path"],
    )


def _parse_results_jsonl(text: str) -> List[dict]:
    results: List[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        results.append(json.loads(line))
    return results


def _rehydrate_results(
    results: List[dict],
) -> List[Tuple[Tuple[Term, Term], BatteryResult]]:
    hydrated: List[Tuple[Tuple[Term, Term], BatteryResult]] = []
    for entry in results:
        axiom_data = entry["axiom"]
        left = Term.parse(axiom_data["left"])
        right = Term.parse(axiom_data["right"])
        features = SyntacticFeatures(**entry["features"])
        degeneracy = DegeneracyReport(**entry["degeneracy"])
        model_spectrum = [ModelSpectrumEntry(**item) for item in entry["model_spectrum"]]
        implications = [_implication_from_dict(item) for item in entry["implications"]]
        perturbation_neighbors = [
            _perturbation_neighbor_from_dict(item)
            for item in entry.get("perturbation_neighbors", [])
        ]
        metrics = entry.get("metrics")
        computed = compute_metrics(
            features,
            degeneracy,
            model_spectrum,
            implications,
            entry["smallest_model_size"],
            perturbation_neighbors=perturbation_neighbors,
        )
        if metrics is None:
            metrics = computed
        else:
            for key, value in computed.items():
                metrics.setdefault(key, value)
        hydrated.append(
            (
                (left, right),
                BatteryResult(
                    features=features,
                    degeneracy=degeneracy,
                    model_spectrum=model_spectrum,
                    smallest_model_size=entry["smallest_model_size"],
                    implications=implications,
                    perturbation_neighbors=perturbation_neighbors,
                    metrics=metrics,
                ),
            )
        )
    return hydrated


def _implication_from_dict(data: dict) -> ImplicationProbe:
    steps = None
    if data.get("proof_steps") is not None:
        steps = [
            ProofStep(step["rule"], step["left"], step["right"])
            for step in data["proof_steps"]
        ]
    return ImplicationProbe(
        theory=data["theory"],
        status=data["status"],
        checked_max_size=data["checked_max_size"],
        counterexample_size=data["counterexample_size"],
        counterexample_fingerprint=data["counterexample_fingerprint"],
        proof_status=data.get("proof_status"),
        proof_elapsed_seconds=data.get("proof_elapsed_seconds"),
        proof_steps=steps,
    )


def _perturbation_neighbor_from_dict(data: dict) -> PerturbationNeighbor:
    return PerturbationNeighbor(
        left=Term.parse(data["left"]),
        right=Term.parse(data["right"]),
        model_statuses=list(data["model_statuses"]),
        smallest_model_size=data["smallest_model_size"],
    )
