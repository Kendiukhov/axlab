# Reproduction & Storage

The artifact store persists battery outputs as content-addressed blobs with a small
SQLite index for run metadata.

## Layout

- `store.db`: SQLite catalog of artifacts and runs.
- `artifacts/`: content-addressed payloads by SHA-256 digest.

## Run Records

Each run record includes:

- `run_id`
- `spec` and `battery_config` JSON
- `manifest_digest` and `results_digest`

## Usage

- Use `ArtifactStore.write_bytes` or `ArtifactStore.write_json` to persist artifacts.
- `run_battery_and_persist(..., store=ArtifactStore(path))` writes the manifest and
  results into the store and adds a run record.
- `load_run_from_store(store, run_id)` rehydrates results from stored JSONL blobs.
- `load_results_as_battery(path)` converts a results file into `BatteryResult` objects.

Each `results.jsonl` entry includes a `metrics` object derived from the battery output,
and these values are also persisted into the `metrics` table when a store is used.

## CLI Runner

Use the CLI runner to enumerate axioms and persist a run:

```sh
python3 -m axlab.cli.run_battery --spec docs/universe_spec.example.json --output runs/run-0001
```

Add `--store path/to/store` to persist the run into the content-addressed store.

Use the replay CLI to rehydrate a stored run into JSON:

```sh
python3 -m axlab.cli.replay_run --store path/to/store --run-id <run_id> --output runs/run-0001.json
```

Use the interpret CLI to emit a theory dossier for a selected axiom:

```sh
python3 -m axlab.cli.interpret --run-dir runs/run-0001 --axiom-left x0 --axiom-right x0 --output runs/dossier.json
```

Add `--store path/to/store --run-id <run_id>` instead of `--run-dir` to load from the store.

The output JSON follows the interpret response contract:

- From a run: `{"run_id": "...", "axiom_id": "...", "dossier": {...}}`
- Direct axiom: `{"axiom_id": "...", "dossier": {...}}`

When using `--run-dir` or `--store/--run-id`, provide either `--axiom-id` or
`--axiom-left`/`--axiom-right` to select the axiom in the run.
