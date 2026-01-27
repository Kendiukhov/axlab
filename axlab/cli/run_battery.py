from __future__ import annotations

import argparse
import itertools
from pathlib import Path
from typing import Iterable, Tuple

from axlab.core.enumerator import enumerate_axioms
from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.pipeline.battery import BatteryConfig
from axlab.pipeline.runner import run_battery_and_persist
from axlab.store import ArtifactStore


def _limit_axioms(
    axioms: Iterable[Tuple[Term, Term]], limit: int | None
) -> Iterable[Tuple[Term, Term]]:
    if limit is None:
        return axioms
    return itertools.islice(axioms, limit)


def _build_config(args: argparse.Namespace) -> BatteryConfig:
    base = BatteryConfig()
    overrides = {}
    if args.max_model_size is not None:
        overrides["max_model_size"] = args.max_model_size
    if args.max_model_seconds is not None:
        overrides["max_model_seconds"] = args.max_model_seconds
    if args.max_model_candidates is not None:
        overrides["max_model_candidates"] = args.max_model_candidates
    if args.implication_max_model_size is not None:
        overrides["implication_max_model_size"] = args.implication_max_model_size
    if args.implication_max_model_seconds is not None:
        overrides["implication_max_model_seconds"] = args.implication_max_model_seconds
    if args.implication_max_model_candidates is not None:
        overrides["implication_max_model_candidates"] = args.implication_max_model_candidates
    if args.perturbation_max_model_size is not None:
        overrides["perturbation_max_model_size"] = args.perturbation_max_model_size
    if args.perturbation_max_model_seconds is not None:
        overrides["perturbation_max_model_seconds"] = args.perturbation_max_model_seconds
    if args.perturbation_max_model_candidates is not None:
        overrides["perturbation_max_model_candidates"] = args.perturbation_max_model_candidates
    if not overrides:
        return base
    data = base.__dict__.copy()
    data.update(overrides)
    return BatteryConfig(**data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the battery and persist results.")
    parser.add_argument("--spec", required=True, help="Path to UniverseSpec JSON.")
    parser.add_argument("--output", required=True, help="Directory for run outputs.")
    parser.add_argument("--store", help="ArtifactStore root directory.")
    parser.add_argument("--limit", type=int, help="Limit number of axioms enumerated.")
    parser.add_argument(
        "--max-model-size",
        type=int,
        help="Override BatteryConfig.max_model_size.",
    )
    parser.add_argument(
        "--max-model-seconds",
        type=float,
        help="Override BatteryConfig.max_model_seconds.",
    )
    parser.add_argument(
        "--max-model-candidates",
        type=int,
        help="Override BatteryConfig.max_model_candidates.",
    )
    parser.add_argument(
        "--implication-max-model-size",
        type=int,
        help="Override BatteryConfig.implication_max_model_size.",
    )
    parser.add_argument(
        "--implication-max-model-seconds",
        type=float,
        help="Override BatteryConfig.implication_max_model_seconds.",
    )
    parser.add_argument(
        "--implication-max-model-candidates",
        type=int,
        help="Override BatteryConfig.implication_max_model_candidates.",
    )
    parser.add_argument(
        "--perturbation-max-model-size",
        type=int,
        help="Override BatteryConfig.perturbation_max_model_size.",
    )
    parser.add_argument(
        "--perturbation-max-model-seconds",
        type=float,
        help="Override BatteryConfig.perturbation_max_model_seconds.",
    )
    parser.add_argument(
        "--perturbation-max-model-candidates",
        type=int,
        help="Override BatteryConfig.perturbation_max_model_candidates.",
    )
    args = parser.parse_args(argv)

    spec = UniverseSpec.load_json(args.spec)
    axioms = _limit_axioms(enumerate_axioms(spec), args.limit)
    output_dir = Path(args.output)
    store = ArtifactStore(args.store) if args.store else None
    config = _build_config(args)
    run_battery_and_persist(spec, axioms, output_dir, config=config, store=store)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
