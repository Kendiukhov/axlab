from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.interpretation import InterpretationConfig, interpret_axiom
from axlab.pipeline.battery import BatteryConfig, BatteryResult, analyze_axiom
from axlab.pipeline.runner import (
    compute_axiom_id,
    load_results_as_battery,
    load_run_from_store,
    load_run_manifest,
    resolve_results_path,
)
from axlab.store import ArtifactStore
from axlab.interpretation.validation import validate_dossier_citations


def _stable_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _overrides_from_args(args: argparse.Namespace) -> Dict[str, object]:
    overrides: Dict[str, object] = {}
    if args.max_model_size is not None:
        overrides["max_model_size"] = args.max_model_size
    if args.max_model_candidates is not None:
        overrides["max_model_candidates"] = args.max_model_candidates
    if args.max_model_seconds is not None:
        overrides["max_model_seconds"] = args.max_model_seconds
    if args.neighbor_count is not None:
        overrides["neighbor_count"] = args.neighbor_count
    return overrides


def _config_from_manifest(manifest_battery: dict, overrides: Dict[str, object]) -> InterpretationConfig:
    battery_config = BatteryConfig(**manifest_battery)
    config = InterpretationConfig.from_battery_config(battery_config)
    return config.override(overrides)


def _config_from_args(overrides: Dict[str, object]) -> InterpretationConfig:
    base = BatteryConfig()
    config = InterpretationConfig.from_battery_config(base)
    return config.override(overrides)


def _battery_config_for_direct(overrides: Dict[str, object]) -> BatteryConfig:
    base = BatteryConfig()
    return BatteryConfig(
        max_model_size=int(overrides.get("max_model_size", base.max_model_size)),
        max_model_candidates=int(overrides.get("max_model_candidates", base.max_model_candidates)),
        max_model_seconds=float(overrides.get("max_model_seconds", base.max_model_seconds)),
        implication_max_model_size=base.implication_max_model_size,
        implication_max_model_candidates=base.implication_max_model_candidates,
        implication_max_model_seconds=base.implication_max_model_seconds,
    )


def _resolve_target_axiom(
    results: List[Tuple[Tuple[Term, Term], BatteryResult]],
    axiom_id: Optional[str],
    axiom_left: Optional[str],
    axiom_right: Optional[str],
) -> Tuple[str, Tuple[Term, Term], BatteryResult, List[Tuple[str, Tuple[Term, Term], BatteryResult]]]:
    target_terms: Optional[Tuple[Term, Term]] = None
    target_result: Optional[BatteryResult] = None
    target_axiom_id: Optional[str] = None
    peer_results: List[Tuple[str, Tuple[Term, Term], BatteryResult]] = []
    for (left, right), result in results:
        current_id = compute_axiom_id(left, right)
        peer_results.append((current_id, (left, right), result))
        if axiom_id is not None and current_id == axiom_id:
            target_terms = (left, right)
            target_result = result
            target_axiom_id = current_id
        if axiom_left is not None and axiom_right is not None:
            if left.serialize() == axiom_left and right.serialize() == axiom_right:
                target_terms = (left, right)
                target_result = result
                target_axiom_id = current_id
    if target_terms is None or target_result is None or target_axiom_id is None:
        raise SystemExit("Axiom not found in run results.")
    return target_axiom_id, target_terms, target_result, peer_results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Interpret an axiom into a theory dossier.")
    parser.add_argument("--spec", help="Path to UniverseSpec JSON (for direct axioms).")
    parser.add_argument("--store", help="ArtifactStore root directory.")
    parser.add_argument("--run-id", help="Run identifier to load from the store.")
    parser.add_argument("--run-dir", help="Directory containing run.json and results.jsonl.")
    parser.add_argument("--axiom-id", help="Axiom identifier to interpret.")
    parser.add_argument("--axiom-left", help="Left term of the axiom.")
    parser.add_argument("--axiom-right", help="Right term of the axiom.")
    parser.add_argument("--output", help="Output JSON path (defaults to stdout).")
    parser.add_argument("--max-model-size", type=int, help="Override max model size.")
    parser.add_argument("--max-model-candidates", type=int, help="Override max model candidates.")
    parser.add_argument("--max-model-seconds", type=float, help="Override max model seconds.")
    parser.add_argument("--neighbor-count", type=int, help="Override nearest neighbor count.")
    args = parser.parse_args(argv)

    if args.run_dir and (args.store or args.run_id):
        raise SystemExit("Use either --run-dir or --store/--run-id.")
    if args.store and not args.run_id:
        raise SystemExit("--run-id is required with --store.")
    if args.run_id and not args.store:
        raise SystemExit("--store is required with --run-id.")

    if (args.axiom_left is None) ^ (args.axiom_right is None):
        raise SystemExit("Provide both --axiom-left and --axiom-right.")

    overrides = _overrides_from_args(args)

    if args.run_dir or args.run_id:
        if args.axiom_id is None and args.axiom_left is None:
            raise SystemExit("Provide --axiom-id or --axiom-left/--axiom-right for runs.")
        if args.run_dir:
            run_dir = Path(args.run_dir)
            manifest = load_run_manifest(run_dir / "run.json")
            results_path = resolve_results_path(manifest.results_path, run_dir)
            results = load_results_as_battery(results_path)
        else:
            store = ArtifactStore(args.store)
            manifest, results = load_run_from_store(store, args.run_id)

        config = _config_from_manifest(manifest.battery_config, overrides)
        spec = UniverseSpec.from_dict(manifest.spec)
        axiom_id, target_terms, target_result, peer_results = _resolve_target_axiom(
            results, args.axiom_id, args.axiom_left, args.axiom_right
        )
        dossier = interpret_axiom(
            spec,
            target_terms,
            target_result,
            config,
            peer_results=peer_results,
        )
        dossier_data = dossier.to_dict()
        try:
            validate_dossier_citations(dossier_data)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        payload = {
            "run_id": manifest.run_id,
            "axiom_id": axiom_id,
            "dossier": dossier_data,
        }
    else:
        if args.spec is None:
            raise SystemExit("--spec is required for direct axioms.")
        if args.axiom_left is None or args.axiom_right is None:
            raise SystemExit("Provide --axiom-left and --axiom-right for direct axioms.")
        spec = UniverseSpec.load_json(args.spec)
        battery_config = _battery_config_for_direct(overrides)
        config = _config_from_args(overrides)
        left = Term.parse(args.axiom_left)
        right = Term.parse(args.axiom_right)
        result = analyze_axiom(spec, left, right, battery_config)
        axiom_id = compute_axiom_id(left, right)
        dossier = interpret_axiom(spec, (left, right), result, config, peer_results=None)
        dossier_data = dossier.to_dict()
        try:
            validate_dossier_citations(dossier_data)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        payload = {
            "axiom_id": axiom_id,
            "dossier": dossier_data,
        }

    output_text = _stable_json(payload)
    if args.output:
        Path(args.output).write_text(output_text + "\n", encoding="utf-8")
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
