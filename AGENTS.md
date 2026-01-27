# Codex Agent Notes

## Role
- Assist with repo analysis, planning, and implementation work on request.
- Keep the AutoAgent/environment boundary intact; do not introduce autonomous loops.
- Prefer deterministic, reproducible changes with tests when possible.

## Project Scope (from project vision)
- This repo implements the environment: axiom space engine, experimental battery, storage, and API.
- The AutoAgent that decides exploration policies is external to this repo.
- Focus on small, bounded UniverseSpec exploration with reproducible artifacts.
- Initial universe: equational logic only; single axiom; no constants/predicates/quantifiers.

## Constraints
- Changes must be explicit and validated; no implicit self-modification.
- Keep documentation and code concise and task-oriented.
- Preserve reproducibility and deterministic behavior.
- Explanations must be grounded in computed artifacts (models, proofs, implications).
- Maintain strict agent/environment separation and explicit execution protocols.
 - Deterministic experiments with strict timeouts and structured artifacts.

## Architecture Summary
- Axiom space engine: enumeration, canonicalization, symmetry handling under UniverseSpec.
- Experimental battery: deterministic model finding, implication probes, metrics extraction.
- AutoAgent interface: actions, state, and artifact access for external control.
- Storage: content-addressed artifacts and replayable runs for comparability.

## Interpretation Requirement
- Provide a deterministic theory dossier pipeline when requested.
- Dossier includes canonical axioms, finite semantic profile, derived laws, classifications,
  relationships to known theories, and fact-cited prose.
 - Interpretation toolchain: property checkers, benchmark identities, model pretty-printing,
   implication-based nearest neighbors, and deterministic prose from computed facts.

## Phased Deliverables
- UniverseSpec: schema, grammar, symmetry/canonicalization, enumerator with count tests.
- MVP battery: syntactic features, degeneracy filters, finite model spectrum, implication probes.
- Engines: model finder and prover interfaces with deterministic behavior and artifacts.
- Storage/repro: DB schema, content-addressed artifacts, run replay, regression benchmarks.
- AutoAgent API: actions, state, protocol for external control only.
- Metrics: non-ML interestingness metrics; environment reports metrics, agent decides.

## Maintenance Protocol
- No autonomous self-modification loops; changes only on request.
- Run unit/regression tests for changes; preserve comparability across versions.

## Working Practices
- Read relevant docs before changes.
- Use small, focused edits and describe artifacts produced.
- Surface assumptions and missing context early.
