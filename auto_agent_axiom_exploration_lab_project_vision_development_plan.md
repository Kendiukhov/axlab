# AutoAgent Axiom Exploration Lab

## Project Vision

The AutoAgent Axiom Exploration Lab is an automated scientific instrument for exploring *axiomatic space*. Its purpose is not merely to enumerate formal axiom systems, but to **discover, characterize, relate, and explain** novel formal systems in a way that is meaningful to human mathematics.

The core ambition is to treat axiomatic systems as *objects of empirical study*: generated, experimented upon, compared, evolved, and ultimately interpreted. The project aims to produce a continuously growing “atlas of micro‑theories” — compact formal worlds together with their semantic profiles, relationships, and human‑readable explanations.

Unlike traditional automated theorem proving or conjecture generation, this project focuses on:
- systematic generation of small axiomatic systems,
- large‑scale automated experimentation (models, implications, proof behavior),
- discovery of structure and phase‑like behavior in axiom space,
- and **translation of alien formal systems into human mathematical language**.

**Important architectural boundary:** the autonomous agent (“AutoAgent”) that drives exploration is **external** to this project. This repository implements the *environment, instrumentation, APIs, and artifacts* that AutoAgent operates on. AutoAgent itself — including its long‑running loop, planning logic, and cognition — is assumed to be provided elsewhere.

---

## Guiding Principles

1. **Bounded Universes, Exhaustively Studied**  
   Exploration is always relative to an explicit, finite UniverseSpec (signature, grammar, size bounds). Depth is preferred over vague generality.

2. **Experimentation Before Interpretation**  
   All explanations must be grounded in computed artifacts: models, proofs, counterexamples, implication relations.

3. **Determinism and Reproducibility**  
   Every result must be reproducible from logged inputs, engine versions, and budgets.

4. **Clear Agent–Environment Separation**  
   The system cleanly separates the exploration *environment* (this repository) from the *agent* (AutoAgent) that decides what actions to take.

5. **Self‑Modification with Guardrails**  
   The environment may support maintenance and extension, but any code changes are explicitly requested and validated; no implicit self‑modification loops exist here.

---

## Conceptual Architecture

The system consists of three tightly integrated layers, with a strict agent–environment boundary:

1. **Axiom Space Engine**  
   Formal enumeration, canonicalization, mutation, and comparison of axioms under a fixed UniverseSpec.

2. **Experimental Battery**  
   Deterministic, reproducible experiments: finite model finding, implication testing, proof probing, and metric extraction.

3. **AutoAgent Interface Layer**  
   A well‑defined API and execution protocol through which an *external* AutoAgent selects actions, triggers experiments, requests interpretation, and consumes artifacts.

---

## Initial Exploration Universe (v0)

To ensure tractability and early success, the initial universe is deliberately small:

- Logic: equational logic only
- Signature (choose one):
  - Option A: one binary operation, single axiom, term size ≤ 5
  - Option B: one binary + one unary operation, single axiom, term size ≤ 4
- No constants, no predicates, no quantifiers
- Axiom sets: single axiom only

This universe is fully specified in a machine‑readable **UniverseSpec** file that defines grammar, bounds, symmetry rules, and experimental settings.

---

## Repository Structure

```
axlab/
├── core/
│   ├── universe_spec.py
│   ├── term.py
│   ├── enumerator.py
│   ├── symmetry.py
│   └── canonicalization.py
│
├── engines/
│   ├── model_finder/
│   └── prover/
│
├── pipeline/
│   ├── battery.py
│   ├── runner.py
│   └── metrics.py
│
├── store/
│   ├── store.py
│   └── schema.sql
│
├── api/
│   ├── actions.py
│   ├── state.py
│   └── __init__.py
│
├── interpretation/
│   ├── toolchain.py
│   └── __init__.py
│
└── cli/
    ├── run_battery.py
    ├── replay_run.py
    └── interpret.py

docs/
├── universe_spec.md
├── engine_interfaces.md
├── api_contract.md
├── interpretation.md
└── reproduction.md

tests/
├── api/
├── cli/
├── core/
├── engines/
├── interpretation/
├── pipeline/
├── regression/
└── store/
```

---

## Phase‑by‑Phase Development Plan

### Phase 0: Universe Specification

Deliverables:
- Formal UniverseSpec schema (JSON/YAML)
- Term grammar and AST
- Symmetry and canonicalization rules
- Enumerator with known‑count validation tests

Goal: define *exactly* what exists in the universe.

---

### Phase 1: Experimental Battery (MVP Science)

For each axiom or axiom set, compute:

1. **Syntactic Features**
   - size, depth, variable count, symmetry class

2. **Degeneracy Filters**
   - projection collapse
   - constant collapse
   - immediate trivial identities

3. **Finite Model Spectrum**
   - model existence for sizes n = 1..k
   - canonical fingerprints
   - smallest model size

4. **Implication Probes**
   - test implication vs curated library of known theories

All results are persisted and reproducible.

---

### Phase 2: Engines

Implement clean interfaces for:

- Model finders (SAT/SMT, Mace‑style, or custom finite search)
- Provers (equational rewriting with bounded counterexample search)

Requirements:
- strict timeouts
- deterministic behavior
- structured artifacts (proof steps, counterexample fingerprints)

---

### Phase 3: Storage and Reproducibility

Database tables (current schema in `axlab/store/schema.sql`):
- artifacts
- runs
- axioms
- models
- implications
- metrics
- notes

Features (current implementation):
- content‑addressed artifacts with a SQLite catalog
- run replay via stored manifest/results blobs
- frozen regression fixture (`tests/regression/fixtures/minimal_run`) to validate replay determinism

---

### Phase 4: AutoAgent Interface & Execution Protocol

This project does **not** implement the AutoAgent loop. Instead, it exposes:

- a persistent environment state
- a set of callable actions (state, enumerate, run battery, load run, compare metrics, interpret)
- structured artifacts and metrics

An external AutoAgent:
1. selects candidate axioms or mutations
2. invokes experiments via the API
3. inspects results and metrics
4. decides whether to discard, expand, or request interpretation

Policies for budgets, diversity, and stopping criteria live in the agent, not here.

---

### Phase 5: Interestingness Metrics (v1)

Initial metrics (non‑ML):
- nontrivial model spectrum
- distance from known theories
- proof‑depth proxies
- robustness under perturbation
- novelty vs archive

Selection is Pareto‑based; the environment reports metrics but does not decide preferences.

---

## Human‑Readable Theory Interpretation (Explicit Requirement)

### Interpretation Mode

The environment provides a deterministic **interpretation pipeline** that an external AutoAgent may invoke for selected theories.

It produces a **Theory Dossier** containing:

1. Canonical axioms and minimal bases
2. Finite semantic profile (models, spectra)
3. Derived laws and characteristic lemmas
4. Property classification (associativity‑like, idempotent‑like, etc.) derived from implication probes
5. Relationships to known human theories via implication signatures
6. Candidate interpretations or definitional equivalences via reverse‑implication checks
7. Clear human‑readable explanation grounded in computed facts and proof traces
8. Open questions and next experiments for inconclusive probes

---

### Interpretation Toolchain

Components:

- Property checker library (standard laws via implication probes)
- Benchmark identity suite (bounded model search)
- Model pretty‑printer
- Translation search via reverse implication checks
- Implication‑based nearest‑neighbor classifier (implication signature distance)
- Deterministic narrative compiler (fixed lines with citations)

All explanations must cite internal results.

---

## Maintenance and Extension Protocol

The environment may be extended or refactored, but:
- changes are explicit and externally requested
- all modifications run unit and regression tests
- experimental results remain comparable across versions

There is no autonomous self‑modification loop inside this repository.

---

## Milestones

M1: End‑to‑end run on v0 universe, full battery, stored results

M2: Stable external AutoAgent successfully drives exploration via API

M3: First generated atlas page (mini periodic table)

M4: First publishable theory dossier (novel or clarified)

M5: Extension to richer signature or multi‑axiom systems

---

## Long‑Term Vision

The mature system functions as a continuously usable **axiom telescope**:

- surveying nearby regions of formal possibility space,
- discovering new structural phenomena,
- revealing unexpected equivalences and phase transitions,
- and translating alien formal systems into comprehensible mathematics.

The ultimate success criterion is not volume, but clarity: fewer axioms, better understood.
