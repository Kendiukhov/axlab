# Engine Interfaces

The engine interfaces define deterministic protocols for model finding and proof search.

## Model Finder

Inputs:

- `UniverseSpec`
- Axioms (equations) and optional must-violate target
- `ModelSearchConfig` with max candidates and max seconds

Outputs (`ModelSearchArtifact`):

- `status`: `found`, `not_found`, `timeout`, or `cutoff`
- `size`: domain size checked
- `fingerprint`: canonical table encoding for the first model found
- `candidates`: tables evaluated
- `elapsed_seconds`: wall-clock time spent
- `max_depth`: deepest slot assignment reached (optional)
- `partial_seconds`: time spent in partial consistency checks (optional)

## Prover

Inputs:

- `UniverseSpec`
- Axioms (equations)
- Goal equation
- `ProofSearchConfig` with max seconds, max model size, max model candidates, and
  rewriting limits (`max_steps`, `max_terms`, `rule_ordering`)

Outputs (`ProofArtifact`):

- `status`: `proved`, `disproved`, `timeout`, `unknown`, or `cutoff`
- `elapsed_seconds`: wall-clock time spent
- `proof`: optional serialized proof
- `counterexample`: optional counterexample reference
- `steps`: optional structured `ProofStep` sequence (rule + equation)

All engines must be deterministic for a fixed input ordering and should respect the
deadline in their configuration.

## Rewriting Prover Stub

The `RewritingProver` performs bounded, deterministic rewriting using exact-match
axiom rules (both directions). It reports a structured step trace when it finds a
goal within the configured step and term limits. The prover uses pattern matching
for rule application and allows a configurable rule ordering (`given`, `reverse`,
`shortest_lhs`, `longest_lhs`) to keep runs deterministic.
