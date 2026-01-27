# Interpretation Pipeline

The interpretation pipeline produces a deterministic **Theory Dossier** for a selected axiom.
It compiles computed artifacts into a human-readable summary while preserving provenance
through citations (e.g., `implication.associative`, `models.spectrum`).

All interpretive claims must be grounded in computed artifacts (models, proofs,
counterexamples, implications). Narrative lines and facts must include citations
that point to their computed sources.

## Toolchain Components

- Property checker library: uses implication probes against standard laws (associative, commutative, idempotent, projections, unary idempotent/involutive).
- Benchmark identity suite: tests additional identities (distributive, absorption, medial).
- Model pretty-printer: renders finite models from the stored fingerprints.
- Translation search: checks definitional equivalence with known theories by probing the reverse implication.
- Implication-based nearest-neighbor classifier: compares implication signatures across axioms in the run.
- Deterministic narrative compiler: emits a fixed set of narrative lines from computed facts.

## Interpret Action Payload

`interpret` accepts either a standalone axiom or a run context:

- `axiom`: `{left, right}` to analyze a single axiom without a run.
- `run_id`: load a stored run (requires a configured store) and interpret an axiom from it.
- `run_dir`: load a run from disk (expects `run.json` + `results.jsonl`).
- `axiom_id`: optional when using `run_id` or `run_dir`; selects an axiom by its computed id.

When `run_id` or `run_dir` is provided, you must also supply either `axiom_id` or `axiom`.

Config overrides can be supplied as either:

- `config`: object with `max_model_size`, `max_model_candidates`, `max_model_seconds`, `neighbor_count`.
- top-level keys: the same config keys merged in directly.

## Theory Dossier Fields

The dossier emitted by `interpret` contains:

- `axiom`, `canonical_axiom`, `minimal_basis`
- `features`, `degeneracy`, `model_spectrum`
- `model_pretty`: human-readable model tables
- `properties`: implication probe outcomes
- `benchmark_identities`: additional identity checks
- `derived_laws`: confirmed properties/benchmarks
- `translations`: definitional equivalence checks
- `nearest_neighbors`: closest implication profiles in the run
- `facts`: cited facts for the narrative, each with a computed source
- `narrative`: deterministic prose lines with citations to computed artifacts
- `open_questions`: unresolved probes to prioritize next

## Interpret Action Response

Responses include a `dossier` plus identifying fields:

- When interpreting from a run: `{run_id, axiom_id, dossier}`.
- When interpreting a standalone axiom: `{axiom_id, dossier}`.

All output is deterministic for fixed inputs and search limits.

## Example Dossier Payload

```json
{
  "axiom": {"left": "f(x0,x0)", "right": "x0"},
  "canonical_axiom": {"left": "f(x0,x0)", "right": "x0"},
  "minimal_basis": [{"left": "f(x0,x0)", "right": "x0"}],
  "features": {"term_size": 3, "var_count": 1},
  "degeneracy": {"projection_collapse": false},
  "model_spectrum": [{"size": 1, "exists": true, "fingerprint": "m1:0000"}],
  "model_pretty": [{"size": 1, "fingerprint": "m1:0000", "lines": ["f(0,0)=0"]}],
  "properties": [
    {
      "name": "idempotent",
      "status": "confirmed",
      "counterexample_size": null,
      "counterexample_fingerprint": null,
      "proof_status": "proved",
      "proof_steps": [{"rule": "axiom", "left": "f(x0,x0)", "right": "x0"}]
    }
  ],
  "benchmark_identities": [
    {
      "name": "left_absorption",
      "left": "f(x0,f(x0,x1))",
      "right": "x0",
      "status": "counterexample",
      "counterexample_size": 2,
      "counterexample_fingerprint": "m2:abcd"
    }
  ],
  "derived_laws": [{"statement": "idempotent confirmed", "source": "implication.idempotent"}],
  "translations": [
    {
      "theory": "semilattice",
      "axiom_implies": "confirmed",
      "theory_implies": "counterexample",
      "status": "inconclusive",
      "counterexample_size": 2,
      "counterexample_fingerprint": "m2:abcd"
    }
  ],
  "nearest_neighbors": [
    {
      "axiom_id": "ax-01",
      "left": "f(x0,x1)",
      "right": "f(x1,x0)",
      "distance": 1.0,
      "shared_confirmed": ["idempotent"]
    }
  ],
  "facts": [{"statement": "smallest model size 1", "source": "models.spectrum"}],
  "narrative": [
    "Canonical axiom: f(x0,x0) = x0 [axiom]",
    "Smallest model found at size 1 [models.spectrum]"
  ],
  "open_questions": ["Resolve benchmark left_absorption with larger model search."]
}
```

## Worked Example (End-to-End Demo)

This repository includes a tiny, deterministic fixture that runs the full pipeline
(enumerate -> battery -> replay -> interpret) on the first two axioms from the example
UniverseSpec. The artifacts live under `docs/fixtures/interpretation_demo/`.

Reproduce the fixture:

```sh
python3 -m axlab.cli.run_battery \
  --spec docs/universe_spec.example.json \
  --output docs/fixtures/interpretation_demo/run \
  --limit 2

python3 -m axlab.cli.replay_run \
  --run-dir docs/fixtures/interpretation_demo/run \
  --output docs/fixtures/interpretation_demo/replay.json

python3 -m axlab.cli.interpret \
  --run-dir docs/fixtures/interpretation_demo/run \
  --axiom-left "x0" \
  --axiom-right "x0" \
  --output docs/fixtures/interpretation_demo/dossier.json
```

Fixture artifacts:

- `docs/fixtures/interpretation_demo/run/run.json` (manifest)
- `docs/fixtures/interpretation_demo/run/results.jsonl` (battery outputs)
- `docs/fixtures/interpretation_demo/dossier.json` (theory dossier)
- `docs/fixtures/interpretation_demo/replay.json` (hydrated replay)

Manifest excerpt (from `run.json`):

```json
{"run_id":"09538223ea8d10d1","axiom_count":2,"results_path":"docs/fixtures/interpretation_demo/run/results.jsonl"}
```

Selected dossier facts (from `dossier.json`):

```json
{
  "axiom_id": "e9bf021bfe781b6e88171c0b2e564758fbbf38ec325b8aeae13bb39ed1d40e8c",
  "axiom": {"left": "x0", "right": "x0"},
  "model_spectrum": [{"size": 1, "status": "found"}],
  "narrative": [
    "Canonical axiom: x0 = x0 [axiom]",
    "Smallest model found at size 1 [models.spectrum]"
  ]
}
```

The dossier values are grounded in the stored model spectrum, implication probes, and
nearest-neighbor comparisons from the run outputs, so re-running the commands above should
produce byte-for-byte identical JSON payloads.
