# Experimental Battery (MVP)

The MVP battery computes deterministic, reproducible artifacts for a single axiom.

## Outputs

- Syntactic features: sizes, depths, distinct variable count, canonical symmetry class.
- Degeneracy filters: trivial identities, projection collapse, constant collapse.
- Finite model spectrum: model existence for sizes 1..k with a fingerprint for the first model found.
- Implication probes: counterexample search against a small library of known theories,
  plus optional proof traces for confirmed implications.
- Perturbation neighbors: deterministic nearby axioms with their model status signatures.
- Metrics: derived interestingness scores and counts computed from features, model spectra,
  and implication results.
- Persistence: `run.json` manifest plus `results.jsonl` with one record per axiom. When an
  `ArtifactStore` is provided, both files are content-addressed and recorded in the store.

## Determinism

- Canonicalization normalizes variable names and commutative operation arguments.
- Model search is exhaustive up to configured cutoffs and iterates in a fixed order.
- Run IDs are derived from the UniverseSpec, battery config, and ordered axiom list.

## Implication Probe Status

- `confirmed`: no counterexample found up to the configured size bound.
- `counterexample`: a model satisfies the axiom but violates the target theory.
- `inconclusive`: search hit a timeout or candidate cutoff before finding a counterexample.

Confirmed probes may include `proof_status`, `proof_elapsed_seconds`, and structured
`proof_steps` when the rewriting prover can derive the target law.

## Metrics

Metrics are computed by `axlab.pipeline.metrics.compute_metrics` and included in each
`results.jsonl` record under the `metrics` key. Stored runs also persist metrics in the
`metrics` table for easy comparison. The metrics include:

- Syntactic complexity: sizes, depths, variable count, and a combined `syntactic_complexity`.
- Degeneracy flags: `trivial_identity`, `projection_collapse`, `constant_collapse`.
- Model spectrum aggregates: found/not_found/timeout/cutoff counts, totals, elapsed time,
  `nontrivial_model_spectrum`, and decisive ratios used as a fallback robustness proxy.
- Implication aggregates: confirmed/counterexample/inconclusive counts and ratios, plus proof counts.
- Proof depth proxies: `proof_step_total`, `proof_step_mean`, `proof_step_max`.
- Distance from known theories: `known_theory_distance` weighted by counterexamples/inconclusive probes.
- Novelty vs archive: `novelty_vs_archive` when archive lookup is available (1.0 if the symmetry class is new, 0.0 if it already exists in the store).
- Perturbation robustness: neighbor counts plus signature agreement and exact match ratios derived
  from the deterministic neighbor spectrum.
