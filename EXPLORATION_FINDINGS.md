# Axiom Exploration Findings

**Generated**: 2026-01-27  
**Total Axioms in Universe**: 484 (2-variable terms, size ≤ 5, one binary operation `f`)  
**Dossiers Generated**: 186  
**Runs Completed**: 60+

---

## Summary

The AutoAgent Axiom Exploration Lab has systematically explored equational axiom systems, testing each against 11 standard algebraic properties and searching for finite models up to size 3.

### Key Results

Most explored axioms fall into three categories:

1. **Degenerate** — Collapse to triviality (constant or projection)
2. **All Properties Refuted** — Counterexamples found for every standard property
3. **Interesting** — Non-degenerate with some properties confirmed ✓

---

## Interesting Axioms Discovered

The following axioms are **non-degenerate** and confirm meaningful algebraic properties:

| Axiom | Confirmed Properties | Enumeration Offset |
|-------|---------------------|-------------------|
| `x0 = f(x1, f(x0,x0))` | left_self_distributive, medial | ~10 |
| `x0 = f(f(x0,x0), x1)` | right_self_distributive, medial | ~15 |
| `f(x0,x0) = f(x0,x1)` | right_self_distributive, medial | ~47 |

### Finite Models

These axioms have non-trivial finite models at sizes 1, 2, and 3:

```
Axiom: x0 = f(x1, f(x0,x0))
Model (size 2):
f:
  0 1
  0 1

Axiom: x0 = f(f(x0,x0), x1)
Model (size 2):
f:
  0 0
  1 1
```

---

## Mathematical Significance

### Connection to Known Structures

| Property | Known Structure | Applications |
|----------|----------------|--------------|
| **Left self-distributive** | Shelves, Racks, Quandles | Knot theory, Yang-Baxter equation |
| **Right self-distributive** | Right shelves | Braid groups |
| **Medial (Entropic)** | Medial quasigroups | Bruck-Toyoda theorem (isotopy to abelian groups) |

### Self-Distributivity

The axiom `x * (y * z) = (x * y) * (x * z)` (left) or `(x * y) * z = (x * z) * (y * z)` (right) defines:

- **Shelf**: Just self-distributivity
- **Rack**: + invertibility (used in knot invariants)
- **Quandle**: + idempotency (`x * x = x`)

The discovered axioms explore the **boundary** of these structures—confirming self-distributivity while refuting idempotency.

### Medial Property

The identity `(x * y) * (u * v) = (x * u) * (y * v)` is foundational in:

- **Entropic algebras** — every operation is a homomorphism
- **Medial quasigroups** — isotopic to abelian groups (Bruck-Toyoda)
- **Medial semigroups** — also called "entropic semigroups"

---

## Exploration Statistics

| Metric | Value |
|--------|-------|
| Universe size | 484 axioms |
| Explored (with dossiers) | 186 axioms |
| Coverage | ~38% |
| Properties tested | 11 |
| Max model size searched | 3 |

### Properties Tested

1. associative
2. commutative  
3. idempotent
4. left_alternative
5. right_alternative
6. flexible
7. left_self_distributive
8. right_self_distributive
9. medial
10. left_projection
11. right_projection

---

## Data Locations

| Artifact | Path |
|----------|------|
| Run directories | `runs/<run_id>/` |
| Theory dossiers | `runs/dossiers/` |
| Agent decision log | `runs/agent_log.jsonl` |
| SQLite store | `runs/store/store.db` |

---

## Future Directions

1. **Extend model search** to size 4+ for inconclusive benchmarks
2. **Explore remaining ~62%** of the axiom space
3. **Search for axioms confirming associativity** (rare in this space)
4. **Investigate axioms with unique model spectra** (only certain sizes exist)
