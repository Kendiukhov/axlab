from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple

from axlab.core.term import Term
from axlab.interpretation import InterpretationConfig, interpret_axiom
from axlab.interpretation.validation import validate_dossier_citations
from axlab.pipeline.runner import (
    compute_axiom_id,
    compute_run_id,
    load_results,
    load_results_as_battery,
    load_run_from_store,
    load_run_manifest,
    resolve_results_path,
    run_battery_and_persist,
    serialize_battery_results,
)
from axlab.pipeline.battery import analyze_axiom
from axlab.api.state import EnvironmentState


class ActionError(RuntimeError):
    pass


def _finalize_dossier(dossier: Any) -> Dict[str, Any]:
    data = dossier.to_dict()
    try:
        validate_dossier_citations(data)
    except ValueError as exc:
        raise ActionError(str(exc)) from exc
    return data


def dispatch(state: EnvironmentState, request: Dict[str, Any]) -> Dict[str, Any]:
    action = request.get("action")
    payload = request.get("payload", {})
    if action is None:
        return {"status": "error", "error": "Missing action."}
    handler = _HANDLERS.get(action)
    if handler is None:
        return {"status": "error", "error": f"Unknown action: {action}"}
    try:
        data = handler(state, payload)
        return {"status": "ok", "data": data}
    except ActionError as exc:
        return {"status": "error", "error": str(exc)}


def _action_state(state: EnvironmentState, payload: Dict[str, Any]) -> Dict[str, Any]:
    return state.to_dict()


def _action_enumerate(state: EnvironmentState, payload: Dict[str, Any]) -> Dict[str, Any]:
    limit = int(payload.get("limit", 100))
    offset = int(payload.get("offset", 0))
    axioms = state.axioms_slice(offset, limit)
    serialized = [{"left": left.serialize(), "right": right.serialize()} for left, right in axioms]
    next_offset = min(state.axiom_count, offset + len(axioms))
    return {
        "axioms": serialized,
        "offset": offset,
        "limit": limit,
        "next_offset": next_offset,
        "complete": next_offset >= state.axiom_count,
        "axiom_count": state.axiom_count,
    }


def _parse_axioms(items: Iterable[Dict[str, Any]]) -> List[Tuple[Term, Term]]:
    axioms: List[Tuple[Term, Term]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ActionError("Axiom entries must be objects with left/right.")
        if "left" not in item or "right" not in item:
            raise ActionError("Axiom entries require left and right.")
        axioms.append((Term.parse(str(item["left"])), Term.parse(str(item["right"]))))
    return axioms


def _resolve_axioms(state: EnvironmentState, payload: Dict[str, Any]) -> List[Tuple[Term, Term]]:
    if "axioms" in payload:
        return _parse_axioms(payload["axioms"])
    if "offset" in payload and "limit" in payload:
        offset = int(payload["offset"])
        limit = int(payload["limit"])
        return state.axioms_slice(offset, limit)
    raise ActionError("Provide axioms or offset/limit.")


def _action_run_battery(state: EnvironmentState, payload: Dict[str, Any]) -> Dict[str, Any]:
    axioms = _resolve_axioms(state, payload)
    if not axioms:
        raise ActionError("No axioms provided.")
    run_id = compute_run_id(state.spec, axioms, state.battery_config)
    output_dir = state.output_root / run_id
    manifest = run_battery_and_persist(
        state.spec,
        axioms,
        output_dir,
        config=state.battery_config,
        store=state.store,
    )
    state.run_history.append(manifest.run_id)
    return {
        "run_id": manifest.run_id,
        "axiom_count": manifest.axiom_count,
        "results_path": manifest.results_path,
    }


def _action_load_run(state: EnvironmentState, payload: Dict[str, Any]) -> Dict[str, Any]:
    include_results = bool(payload.get("include_results", False))
    run_id = payload.get("run_id")
    run_dir = payload.get("run_dir")
    if run_id is not None:
        if state.store is None:
            raise ActionError("Store is required to load by run_id.")
        manifest, hydrated = load_run_from_store(state.store, str(run_id))
        results_path = manifest.results_path
        data = {
            "manifest": manifest.__dict__,
            "results_path": results_path,
        }
        if include_results:
            data["results"] = serialize_battery_results(hydrated)
        return data
    if run_dir is not None:
        manifest = load_run_manifest(Path(run_dir) / "run.json")
        results_path = resolve_results_path(manifest.results_path, run_dir)
        data = {"manifest": manifest.__dict__, "results_path": manifest.results_path}
        if include_results:
            data["results"] = load_results(results_path)
        return data
    raise ActionError("Provide run_id or run_dir.")


def _action_replay_run(state: EnvironmentState, payload: Dict[str, Any]) -> Dict[str, Any]:
    run_id = payload.get("run_id")
    run_dir = payload.get("run_dir")
    if run_id is not None:
        if state.store is None:
            raise ActionError("Store is required to load by run_id.")
        manifest, results = load_run_from_store(state.store, str(run_id))
        return {
            "manifest": manifest.__dict__,
            "results": serialize_battery_results(results),
        }
    if run_dir is not None:
        manifest = load_run_manifest(Path(run_dir) / "run.json")
        results_path = resolve_results_path(manifest.results_path, run_dir)
        results = load_results_as_battery(results_path)
        return {
            "manifest": manifest.__dict__,
            "results": serialize_battery_results(results),
        }
    raise ActionError("Provide run_id or run_dir.")


def _action_compare_metrics(state: EnvironmentState, payload: Dict[str, Any]) -> Dict[str, Any]:
    if state.store is None:
        raise ActionError("Store is required to compare metrics.")
    run_id = payload.get("run_id")
    axiom_a = payload.get("axiom_a")
    axiom_b = payload.get("axiom_b")
    if run_id is None or axiom_a is None or axiom_b is None:
        raise ActionError("run_id, axiom_a, and axiom_b are required.")
    axioms = _parse_axioms([axiom_a, axiom_b])
    axiom_id_a = compute_axiom_id(axioms[0][0], axioms[0][1])
    axiom_id_b = compute_axiom_id(axioms[1][0], axioms[1][1])
    metrics_a = state.store.load_metrics(str(run_id), axiom_id_a)
    metrics_b = state.store.load_metrics(str(run_id), axiom_id_b)
    delta: Dict[str, Any] = {}
    equal: Dict[str, bool] = {}
    for key in sorted(set(metrics_a) | set(metrics_b)):
        left = metrics_a.get(key)
        right = metrics_b.get(key)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            delta[key] = right - left
            equal[key] = left == right
        else:
            delta[key] = None
            equal[key] = left == right
    return {
        "metrics_a": metrics_a,
        "metrics_b": metrics_b,
        "delta": delta,
        "equal": equal,
    }


def _action_interpret(state: EnvironmentState, payload: Dict[str, Any]) -> Dict[str, Any]:
    config = InterpretationConfig.from_battery_config(state.battery_config)
    config_payload = payload.get("config")
    if isinstance(config_payload, dict):
        config = config.override(config_payload)
    else:
        config = config.override(payload)

    target_axiom = payload.get("axiom")
    target_axiom_id = payload.get("axiom_id")
    run_id = payload.get("run_id")
    run_dir = payload.get("run_dir")
    if target_axiom is not None and not isinstance(target_axiom, dict):
        raise ActionError("Axiom entries must be objects with left/right.")

    if run_id is not None:
        if state.store is None:
            raise ActionError("Store is required to load by run_id.")
        manifest, results = load_run_from_store(state.store, str(run_id))
        peer_results: List[Tuple[str, Tuple[Term, Term], Any]] = []
        target_result = None
        target_terms = None
        for (left, right), result in results:
            axiom_id = compute_axiom_id(left, right)
            peer_results.append((axiom_id, (left, right), result))
            if target_axiom_id is not None and axiom_id == target_axiom_id:
                target_result = result
                target_terms = (left, right)
            if target_axiom is not None:
                if left.serialize() == str(target_axiom.get("left")) and right.serialize() == str(
                    target_axiom.get("right")
                ):
                    target_result = result
                    target_terms = (left, right)
                    target_axiom_id = axiom_id
        if target_result is None or target_terms is None:
            raise ActionError("Axiom not found in run results.")
        dossier = interpret_axiom(
            state.spec,
            target_terms,
            target_result,
            config,
            peer_results=peer_results,
        )
        return {
            "run_id": manifest.run_id,
            "axiom_id": target_axiom_id,
            "dossier": _finalize_dossier(dossier),
        }

    if run_dir is not None:
        manifest = load_run_manifest(Path(run_dir) / "run.json")
        results_path = resolve_results_path(manifest.results_path, run_dir)
        results = load_results_as_battery(results_path)
        peer_results = []
        target_result = None
        target_terms = None
        for (left, right), result in results:
            axiom_id = compute_axiom_id(left, right)
            peer_results.append((axiom_id, (left, right), result))
            if target_axiom is not None:
                if left.serialize() == str(target_axiom.get("left")) and right.serialize() == str(
                    target_axiom.get("right")
                ):
                    target_result = result
                    target_terms = (left, right)
                    target_axiom_id = axiom_id
            if target_axiom_id is not None and axiom_id == target_axiom_id:
                target_result = result
                target_terms = (left, right)
        if target_result is None or target_terms is None:
            raise ActionError("Axiom not found in run results.")
        dossier = interpret_axiom(
            state.spec,
            target_terms,
            target_result,
            config,
            peer_results=peer_results,
        )
        return {
            "run_id": manifest.run_id,
            "axiom_id": target_axiom_id,
            "dossier": _finalize_dossier(dossier),
        }

    if target_axiom is None:
        raise ActionError("Provide axiom, run_id, or run_dir.")
    if "left" not in target_axiom or "right" not in target_axiom:
        raise ActionError("Axiom entries require left and right.")
    left = Term.parse(str(target_axiom["left"]))
    right = Term.parse(str(target_axiom["right"]))
    result = analyze_axiom(state.spec, left, right, state.battery_config)
    axiom_id = compute_axiom_id(left, right)
    dossier = interpret_axiom(state.spec, (left, right), result, config, peer_results=None)
    return {"axiom_id": axiom_id, "dossier": _finalize_dossier(dossier)}


_HANDLERS: Dict[str, Callable[[EnvironmentState, Dict[str, Any]], Dict[str, Any]]] = {
    "state": _action_state,
    "enumerate": _action_enumerate,
    "run_battery": _action_run_battery,
    "run": _action_run_battery,
    "load_run": _action_load_run,
    "replay_run": _action_replay_run,
    "compare_metrics": _action_compare_metrics,
    "compare": _action_compare_metrics,
    "interpret": _action_interpret,
}
