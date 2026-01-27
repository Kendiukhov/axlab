from __future__ import annotations

import argparse
import json
from pathlib import Path

from axlab.pipeline.runner import (
    load_results_as_battery,
    load_run_from_store,
    load_run_manifest,
    resolve_results_path,
    serialize_battery_results,
)
from axlab.store import ArtifactStore


def _stable_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay a persisted run to JSON.")
    parser.add_argument("--store", help="ArtifactStore root directory.")
    parser.add_argument("--run-id", help="Run identifier to load from the store.")
    parser.add_argument("--run-dir", help="Directory containing run.json and results.jsonl.")
    parser.add_argument("--output", help="Output JSON path (defaults to stdout).")
    args = parser.parse_args(argv)

    if args.run_dir and (args.store or args.run_id):
        raise SystemExit("Use either --run-dir or --store/--run-id.")
    if args.store and not args.run_id:
        raise SystemExit("--run-id is required with --store.")
    if not args.run_dir and not args.store:
        raise SystemExit("Provide --run-dir or --store/--run-id.")

    if args.run_dir:
        run_dir = Path(args.run_dir)
        manifest = load_run_manifest(run_dir / "run.json")
        results_path = resolve_results_path(manifest.results_path, run_dir)
        results = load_results_as_battery(results_path)
    else:
        store = ArtifactStore(args.store)
        manifest, results = load_run_from_store(store, args.run_id)

    payload = {
        "manifest": manifest.__dict__,
        "results": serialize_battery_results(results),
    }
    output_text = _stable_json(payload)
    if args.output:
        Path(args.output).write_text(output_text + "\n", encoding="utf-8")
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
