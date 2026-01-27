# AutoAgent Environment API Contract

This API is a local, in-process protocol intended for an external AutoAgent to call.
Requests and responses are plain dictionaries passed to `axlab.api.dispatch`.

## AutoAgent Execution Protocol (Concrete)

Use the environment as a deterministic service and keep policy decisions external.
At a minimum, every AutoAgent cycle should capture: the input axiom(s), the run_id,
the metrics used to decide, and any interpretation/compare outputs.

1) Initialize
   - Call `state` and persist the returned `spec`, `battery_config`, and `axiom_count`.
   - Treat these as immutable inputs for the exploration session.
2) Enumerate deterministically
   - Call `enumerate` with `offset`/`limit`.
   - Store the offsets you have already consumed to avoid duplication.
3) Select a batch (policy-side)
   - Choose axioms by a deterministic policy (e.g., top-k by a metric, or breadth-first).
   - Record the policy inputs and any tie-break logic.
4) Run the battery
   - Use API `run`/`run_battery` or CLI `axlab.cli.run_battery`.
   - A `run_id` is a stable hash of `(spec, config, axioms)`.
5) Analyze results
   - Parse `results.jsonl` and rank or filter using `metrics`.
   - Persist the scoring inputs and the resulting ranking externally.
6) Compare candidates
   - Use API `compare` (requires store) to get per-metric deltas.
7) Interpret a short list
   - Use API `interpret` or CLI `axlab.cli.interpret` to produce a Theory Dossier.
8) Decide and checkpoint
   - Either expand search, refine candidates, or stop based on budget.
   - Record decisions outside this repository for reproducibility.

## What to Read From `results.jsonl`

Each line is a JSON object with this shape:

```json
{
  "axiom": {"left": "...", "right": "..."},
  "features": { "...": "..." },
  "degeneracy": { "...": "..." },
  "model_spectrum": [ { "...": "..." } ],
  "smallest_model_size": 2,
  "implications": [ { "...": "..." } ],
  "perturbation_neighbors": [ { "...": "..." } ],
  "metrics": { "...": "..." }
}
```

The AutoAgent should treat `metrics` as the primary ranking signals and use
`model_spectrum`, `implications`, and `perturbation_neighbors` for deeper analysis
or to build dossiers for human review.

## Minimal API Loop (Pseudo-code)

```python
state = dispatch(env, {"action": "state"})["data"]
page = dispatch(env, {"action": "enumerate", "payload": {"offset": 0, "limit": 50}})["data"]
run = dispatch(env, {"action": "run", "payload": {"axioms": page["axioms"]}})["data"]
results = dispatch(env, {"action": "load_run", "payload": {"run_dir": run["results_path"].rsplit("/", 1)[0],
                                                         "include_results": True}})["data"]
ranked = rank_by_metrics(results["results"])
top = ranked[:3]
for axiom in top:
    dossier = dispatch(env, {"action": "interpret", "payload": {"axiom": axiom["axiom"],
                                                               "run_dir": run["results_path"].rsplit("/", 1)[0]}})
```

## Request Envelope

```
{
  "action": "<action_name>",
  "payload": { ... }
}
```

## Response Envelope

```
{
  "status": "ok" | "error",
  "data": { ... },     # present when status == "ok"
  "error": "<message>" # present when status == "error"
}
```

## Actions

### `state`
Return the current environment state.

Payload: none

Response data:
- `spec`: UniverseSpec as dict
- `battery_config`: BatteryConfig as dict
- `output_root`: path string
- `store_root`: path string or null
- `run_count`: number of runs executed in this session
- `term_count`: number of terms in the universe
- `axiom_count`: number of axioms in the universe

### `enumerate`
Enumerate axioms deterministically by offset and limit.

Payload:
- `offset` (int, default 0)
- `limit` (int, default 100)

Response data:
- `axioms`: list of `{ "left": "...", "right": "..." }`
- `offset`, `limit`, `next_offset`
- `complete`: whether enumeration is finished
- `axiom_count`

### `run_battery` / `run`
Run the experimental battery on specified axioms and persist results.

Payload:
- `axioms`: list of `{ "left": "...", "right": "..." }`
  - OR `offset` + `limit` to select from enumeration.

Response data:
- `run_id`: stable hash of (spec, config, axioms)
- `axiom_count`: number of axioms run
- `results_path`: path to `results.jsonl`

### `load_run`
Load a run and optionally return results.

Payload:
- `run_id` (requires store)
  - OR `run_dir` pointing to a run directory
- `include_results` (bool, default false)

Response data:
- `manifest`: run manifest dict
- `results_path`
- `results` (optional, list of result entries, same shape as `results.jsonl`)

### `compare_metrics` / `compare`
Compare metrics between two axioms in a stored run.

Payload:
- `run_id`
- `axiom_a`: `{ "left": "...", "right": "..." }`
- `axiom_b`: `{ "left": "...", "right": "..." }`

Response data:
- `metrics_a`, `metrics_b`: per-axiom metrics dicts
- `delta`: numeric differences where available
- `equal`: per-metric equality flags

### `interpret`
Generate a Theory Dossier for a selected axiom. If `run_id`/`run_dir` are omitted, the axiom
is analyzed on the fly and only that axiom is used for peer comparisons.

Payload:
- `axiom`: `{ "left": "...", "right": "..." }`
  - OR `axiom_id` with `run_id` / `run_dir`
- `run_id` (optional, requires store)
- `run_dir` (optional, points at a run directory)
- `config` (optional): overrides for interpretation search limits
  - `max_model_size`, `max_model_candidates`, `max_model_seconds`, `neighbor_count`
- Alternatively, pass the config override keys at the top level of the payload.

Response data:
- `axiom_id`
- `run_id` (when interpreting from `run_id` or `run_dir`)
- `dossier`: theory dossier dict (see `docs/interpretation.md`), with citations on facts and narrative lines
