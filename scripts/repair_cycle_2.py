import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from axlab.api import EnvironmentState, dispatch
from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.runner import compute_axiom_id

def _stable_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=((",", ":")))

def _score_entry(entry: Dict[str, Any]) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
    metrics = entry.get("metrics", {})
    degeneracy = entry.get("degeneracy", {})
    nontrivial = not (
        degeneracy.get("trivial_identity")
        or degeneracy.get("projection_collapse")
        or degeneracy.get("constant_collapse")
    )
    nontrivial_model = bool(metrics.get("nontrivial_model_spectrum"))
    known_distance = metrics.get("known_theory_distance")
    robustness = metrics.get("robustness_under_perturbation")
    implication_confirmed = metrics.get("implication_confirmed_ratio")
    decisive_ratio = metrics.get("model_decisive_ratio")
    complexity = metrics.get("syntactic_complexity") or 0

    score_components = {
        "nontrivial": int(nontrivial),
        "nontrivial_model_spectrum": int(nontrivial_model),
        "known_theory_distance": known_distance,
        "robustness_under_perturbation": robustness,
        "implication_confirmed_ratio": implication_confirmed,
        "model_decisive_ratio": decisive_ratio,
        "syntactic_complexity": complexity,
    }

    def _metric_or_default(value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        return -1.0

    sort_key = (
        -score_components["nontrivial"],
        -score_components["nontrivial_model_spectrum"],
        -_metric_or_default(score_components["known_theory_distance"]),
        -_metric_or_default(score_components["robustness_under_perturbation"]),
        -_metric_or_default(score_components["implication_confirmed_ratio"]),
        -_metric_or_default(score_components["model_decisive_ratio"]),
        complexity,
    )
    return sort_key, score_components

def _summarize_entry(entry: Dict[str, Any], axiom_id: str) -> Dict[str, Any]:
    model_signature = [item["status"] for item in entry.get("model_spectrum", [])]
    implication_signature = [
        {"theory": item["theory"], "status": item["status"]}
        for item in entry.get("implications", [])
    ]
    perturbation_signatures = [
        {
            "left": item["left"],
            "right": item["right"],
            "model_statuses": list(item.get("model_statuses", [])),
            "smallest_model_size": item.get("smallest_model_size"),
        }
        for item in entry.get("perturbation_neighbors", [])
    ]
    return {
        "axiom": entry.get("axiom"),
        "axiom_id": axiom_id,
        "metrics": entry.get("metrics"),
        "degeneracy": entry.get("degeneracy"),
        "model_signature": model_signature,
        "implication_signature": implication_signature,
        "perturbation_neighbors": perturbation_signatures,
    }

def _rank_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []
    for entry in results:
        axiom = entry["axiom"]
        left = Term.parse(axiom["left"])
        right = Term.parse(axiom["right"])
        axiom_id = compute_axiom_id(left, right)
        sort_key, score_components = _score_entry(entry)
        ranked.append(
            {
                "sort_key": sort_key,
                "score_components": score_components,
                "summary": _summarize_entry(entry, axiom_id),
            }
        )
    ranked.sort(key=lambda item: (item["sort_key"], item["summary"]["axiom_id"]))
    return ranked

def _write_log(log_path: Path, payload: Dict[str, Any]) -> None:
    # log_path.parent.mkdir(parents=True, exist_ok=True) # Assumed exists
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(_stable_json(payload))
        handle.write("\n")

def main():
    cycle_id = 2
    run_id = "ac7e889f08fdeac4"
    log_path = Path("../results/runs/agent_log.jsonl")
    spec_path = "docs/universe_spec.example.json"
    
    spec = UniverseSpec.load_json(spec_path)
    state = EnvironmentState.from_spec(spec, output_root="../results/runs", store_root="../results/runs/store")


    # Load results
    load_response = dispatch(state, {"action": "load_run", "payload": {"run_id": run_id, "include_results": True}})
    results = load_response["data"]["results"]
    ranked = _rank_results(results)

    # Log Analyze
    scoring_policy = {
        "tie_break_rules": [
            "prefer nontrivial axioms (not trivial/projection/constant collapse)",
            "prefer nontrivial model spectrum",
            "prefer larger known_theory_distance",
            "prefer larger robustness_under_perturbation",
            "prefer larger implication_confirmed_ratio",
            "prefer larger model_decisive_ratio",
            "prefer lower syntactic_complexity",
            "tie-break by axiom_id lexicographic",
        ],
        "score_components": [
            "nontrivial",
            "nontrivial_model_spectrum",
            "known_theory_distance",
            "robustness_under_perturbation",
            "implication_confirmed_ratio",
            "model_decisive_ratio",
            "syntactic_complexity",
        ],
    }
    _write_log(
        log_path,
        {
            "cycle": cycle_id,
            "event": "analyze",
            "run_id": run_id,
            "scoring_policy": scoring_policy,
            "ranking": [
                {
                    "axiom": item["summary"]["axiom"],
                    "axiom_id": item["summary"]["axiom_id"],
                    "score_components": item["score_components"],
                    "model_signature": item["summary"]["model_signature"],
                    "implication_signature": item["summary"]["implication_signature"],
                    "perturbation_neighbors": item["summary"]["perturbation_neighbors"],
                }
                for item in ranked
            ],
        },
    )

    # Log Compare
    if len(ranked) >= 2:
        axiom_a = ranked[0]["summary"]["axiom"]
        axiom_b = ranked[1]["summary"]["axiom"]
        compare_response = dispatch(
            state,
            {
                "action": "compare",
                "payload": {
                    "run_id": run_id,
                    "axiom_a": axiom_a,
                    "axiom_b": axiom_b,
                },
            },
        )
        _write_log(
            log_path,
            {
                "cycle": cycle_id,
                "event": "compare",
                "run_id": run_id,
                "axiom_a": axiom_a,
                "axiom_b": axiom_b,
                "metrics_a": compare_response["data"]["metrics_a"],
                "metrics_b": compare_response["data"]["metrics_b"],
                "delta": compare_response["data"]["delta"],
                "equal": compare_response["data"]["equal"],
            },
        )

    # Log Interpret
    dossier_dir = Path("../results/runs/dossiers")
    dossier_dir.mkdir(parents=True, exist_ok=True)
    # Interpret top 1
    item = ranked[0]
    axiom = item["summary"]["axiom"]
    interpret_response = dispatch(
        state,
        {
            "action": "interpret",
            "payload": {"run_id": run_id, "axiom": axiom},
        },
    )
    data = interpret_response["data"]
    dossier_path = dossier_dir / f"dossier-{data['run_id']}-{data['axiom_id']}.json"
    dossier_path.write_text(_stable_json(data["dossier"]) + "\n", encoding="utf-8")
    _write_log(
        log_path,
        {
            "cycle": cycle_id,
            "event": "interpret",
            "run_id": data["run_id"],
            "axiom": axiom,
            "axiom_id": data["axiom_id"],
            "dossier_path": str(dossier_path),
        },
    )

if __name__ == "__main__":
    main()
