# AutoAgent Axiom Exploration Lab

This repository implements the deterministic environment for exploring small
equational axiom systems. It provides UniverseSpec enumeration, a reproducible
experimental battery, artifact storage and replay, an interpretation toolchain,
and a strict in-process API. The external AutoAgent (policy/controller) is out
of scope and must live elsewhere.

## Current State

Implemented and covered by tests (verified in-tree):

- UniverseSpec schema + parser, term grammar/AST, symmetry rules,
  canonicalization, enumerator with count tests, and perturbation neighbors.
- Experimental battery: syntactic features, degeneracy checks, finite model
  spectrum search, implication probes against known-theory libraries, optional
  proof attempts, perturbation robustness probes, and metrics aggregation.
- Engines: naive model finder (with prunable search profiling), naive prover,
  and a rewriting prover with pattern matching and rule ordering policies.
- Artifact store: content-addressed blobs and SQLite tables for runs, axioms,
  models, implications, metrics, and notes; run replay utilities.
- In-process API: state, enumerate, run, load/replay, compare, interpret.
- Interpretation toolchain: theory dossier with properties, benchmarks,
  translations, nearest neighbors, model pretty-printing, and cited narrative
  with citation validation.
- CLI tools: `run_battery`, `replay_run`, `interpret`, `auto_agent_driver`.

Known limits:

- Engines are bounded and naive; they trade completeness/performance for
  determinism.
- API is in-process only (no daemon or network service).
- AutoAgent policy loop and external persistence are not implemented here.
- No networked daemon; all APIs are in-process calls or CLI entry points.
- No third-party dependencies; the codebase uses the Python standard library.

Phase coverage snapshot:

- Phase 0: UniverseSpec schema, parsing, canonicalization, enumeration, and
  count tests.
- Phase 1: battery features, degeneracy filters, finite model spectrum, and
  implication probes with known-theory libraries.
- Phase 2: deterministic model finder + naive/rewrite provers with structured
  artifacts and timeouts.
- Phase 3: content-addressed store, run manifests/results, and replay utilities
  (with regression fixtures).
- Phase 4: in-process API state/actions (no long-running daemon or policy loop).
- Phase 5: non-ML metrics and perturbation robustness (archive novelty is a
  caller-provided hook).

## AutoAgent Role (Detailed)

The AutoAgent is an external policy/controller. It should treat this repo as a
deterministic scientific instrument, keep all decision-making external, and
log every choice it makes so a run is replayable.

What the AutoAgent should do:

1) Initialize and pin inputs
   - Call `state` once and persist `spec`, `battery_config`, and `axiom_count`.
   - These are immutable inputs for the exploration session.
2) Enumerate deterministically
   - Call `enumerate` with `offset`/`limit` and record consumed offsets.
   - Avoid re-ordering; enumeration order is part of reproducibility.
3) Select a batch (policy-side)
   - Choose axioms deterministically (tie-break rules must be logged).
   - Persist policy inputs and chosen axioms outside the environment.
4) Run the battery
   - Call `run` or CLI `axlab.cli.run_battery` to produce `run_id` and results.
   - Persist `run_id`, output paths, and the config used in the agent log.
5) Analyze results
   - Parse `results.jsonl` and rank using `metrics` and implication signatures.
   - Log scoring inputs and the ranking for replayability.
6) Compare candidates
   - Use `compare_metrics` to compute per-metric deltas (requires store).
7) Interpret a shortlist
   - Use `interpret` to produce a theory dossier with cited facts.
   - Dossiers are deterministic summaries meant for human review.
8) Decide and checkpoint
   - Expand, refine, or stop; log decisions, budgets, and offsets externally.

What the AutoAgent must not do:

- Modify environment internals or self-modify code.
- Bypass API/CLI by writing artifacts directly.
- Introduce nondeterministic choices without logging inputs and tie-breaks.

What the AutoAgent must record (minimum):

- UniverseSpec path or digest, battery config, and engine budgets.
- Enumeration offsets/limits consumed (including wrap behavior).
- Policy ranking features and tie-break rules.
- Run identifiers, result paths, and any dossier outputs.

## AutoAgent Workflow (Concrete)

The `axlab.cli.auto_agent_driver` is a deterministic demo of the above protocol.
It does not implement a policy loop; it just shows the expected interaction
pattern and logging format. A typical external loop should mirror it:

1) `state` once per session to pin inputs.
2) `enumerate` with `offset`/`limit` and log the offset window.
3) `run` to create a run directory and (optionally) store entries.
4) `analyze` by ranking `results.jsonl` using metrics.
5) `compare` a shortlist and (optionally) `interpret` top candidates.
6) Repeat with a new offset or stop.

The demo driver writes an append-only JSONL log at `runs/agent_log.jsonl` with
explicit `cycle` numbers so the full policy decision history is replayable.

## Artifacts and Outputs

- Run directory layout: `run.json` (manifest) and `results.jsonl` (one axiom per line).
- Each result entry contains `axiom`, `features`, `degeneracy`, `model_spectrum`,
  `implications`, `perturbation_neighbors`, and `metrics`.
- Proof attempts are embedded in implication probes as `proof_status`, `proof_steps`,
  and `proof_elapsed_seconds` for replayable evidence.
- The optional artifact store mirrors run manifests/results and expands them into
  SQLite tables for axioms, models, implications, metrics, and notes.

## Quickstart

Run the battery on an example spec and persist a run directory:

```sh
python3 -m axlab.cli.run_battery \
  --spec docs/universe_spec.example.json \
  --output runs/run-0001
```

Persist the same run into the artifact store:

```sh
python3 -m axlab.cli.run_battery \
  --spec docs/universe_spec.example.json \
  --output runs/run-0001 \
  --store runs/store
```

Replay a stored run into a single JSON payload:

```sh
python3 -m axlab.cli.replay_run \
  --store runs/store \
  --run-id <run_id> \
  --output runs/run-0001.json
```

Interpret an axiom from a run directory:

```sh
python3 -m axlab.cli.interpret \
  --run-dir runs/run-0001 \
  --axiom-left "f(x0,x0)" \
  --axiom-right "x0" \
  --output runs/dossier.json
```

Run a single deterministic AutoAgent cycle (demo policy only):

```sh
python3 -m axlab.cli.auto_agent_driver \
  --spec docs/universe_spec.example.json \
  --output-root runs \
  --store-root runs/store
```

## API Usage

The API is in-process and uses a request/response envelope:

```python
from axlab.api import EnvironmentState, dispatch
from axlab.core.universe_spec import UniverseSpec

spec = UniverseSpec.load_json("docs/universe_spec.example.json")
state = EnvironmentState.from_spec(spec, output_root="runs", store_root="runs/store")

response = dispatch(state, {"action": "enumerate", "payload": {"offset": 0, "limit": 5}})
```

See `docs/api_contract.md` for the full action surface.

## Repository Layout

- `axlab/core/`: UniverseSpec, term parsing, enumeration, symmetry, canonicalization.
- `axlab/engines/`: model finder and prover interfaces, naive implementations.
- `axlab/pipeline/`: battery, implications, metrics, and run persistence.
- `axlab/store/`: artifact store and SQLite schema.
- `axlab/api/`: in-process API state and action dispatch.
- `axlab/interpretation/`: theory dossier toolchain and validation.
- `axlab/cli/`: `run_battery`, `replay_run`, `interpret`, `auto_agent_driver`.
- `docs/`: specs for UniverseSpec, engines, API, interpretation, reproduction.
- `tests/`: unit, pipeline, store, CLI, API, interpretation, regression.

## Testing

```sh
python3 -m unittest discover -s tests
```

## Documentation

- `docs/universe_spec.md`: UniverseSpec schema overview.
- `docs/experimental_battery.md`: battery outputs and metrics.
- `docs/engine_interfaces.md`: model finder and prover contracts.
- `docs/reproduction.md`: artifact store and replay.
- `docs/api_contract.md`: AutoAgent-facing API.
- `docs/interpretation.md`: theory dossier pipeline.
