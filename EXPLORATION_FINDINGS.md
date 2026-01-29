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
3. **Interesting** — Non-degenerate with some properties confirmed ✓ (234 unique)

---

## Interesting Axioms Discovered

Summary of non-trivial axioms found (234 unique):

| Category | Count | Notable Properties |
|----------|-------|--------------------|
| **Medial (Entropic)** | 125 | `(x*y)*(u*v) = (x*u)*(y*v)` |
| **Self-Distributive** | 112 | Shelves, Racks |
| **Idempotent** | 74 | Quandles, idempotent semigroups |
| **Associative** | 61 | Semigroups, Monoids |
| **Symmetric/Flexible** | 143 | Non-associative symmetry |
| **Other Interesting** | 16 | Left/Right alternative, etc. |

> [!NOTE]
> Counts overlap as some axioms confirm multiple properties (e.g., a commutative associative axiom is both Medial and Idempotent).

---

## Detailed Data and Reports
- **Full Axiom List**: [reports/categorized_axioms_full.txt](file:///Volumes/Crucial%20X6/MacBook/Code/axioms/reports/categorized_axioms_full.txt)
- **Aggregate Statistics**: [reports/STATISTICS.md](file:///Volumes/Crucial%20X6/MacBook/Code/axioms/reports/STATISTICS.md)
- **Visual Dashboard**: ![Axiom Dashboard](file:///Volumes/Crucial%20X6/MacBook/Code/axioms/reports/axiom_dashboard.png)

### Selected Examples

The following axioms are **non-degenerate** and confirm meaningful algebraic properties:

| Axiom | Confirmed Properties |
|-------|---------------------|
| `x0 = f(x1, f(x0,x0))` | left_self_distributive, medial |
| `x0 = f(f(x0,x0), x1)` | right_self_distributive, medial |
| `f(x0,x0) = f(x0,x1)` | right_self_distributive, medial |

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

## Cycle 6 Findings (Offset 88, Limit 16)

1.  **Run ID:** `88276bd29f2f1b0f`
2.  **Top Candidate:** `f(x1,x0) = f(x1,f(x0,x1))` (Axiom ID: `4754e825f26c7b32039ee2188f706fe2e18e64518e539654c215084983d96076`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/88276bd29f2f1b0f/results.jsonl`, dossier generated at `runs/dossiers/dossier-88276bd29f2f1b0f-4754e825f26c7b32039ee2188f706fe2e18e64518e539654c215084983d96076.json`.

## Cycle 7 Findings (Offset 104, Limit 16)

1.  **Run ID:** `319eeacee2f2efdf`
2.  **Top Candidate:** `f(x1,x1) = f(x0,x0)` (Axiom ID: `963248b67fc450b7d1ae23dbffb9588cea72b59e2b08b2e17d76bcecc93599c6`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/319eeacee2f2efdf/results.jsonl`, dossier generated at `runs/dossiers/dossier-319eeacee2f2efdf-963248b67fc450b7d1ae23dbffb9588cea72b59e2b08b2e17d76bcecc93599c6.json`.

## Cycle 8 Findings (Offset 120, Limit 16)

1.  **Run ID:** `c19ff28520499d78`
2.  **Top Candidate:** `f(x1,x1) = f(f(x0,x0),x1)` (Axiom ID: `17a4803826742ddd3bd37d98bfa2d3e8f06509396d412125bacf9238a173b961`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/c19ff28520499d78/results.jsonl`, dossier generated at `runs/dossiers/dossier-c19ff28520499d78-17a4803826742ddd3bd37d98bfa2d3e8f06509396d412125bacf9238a173b961.json`.

## Cycle 9 Findings (Offset 136, Limit 16)

1.  **Run ID:** `20e639b5398aa99f`
2.  **Top Candidate:** `f(x0,f(x0,x0)) = f(x1,x1)` (Axiom ID: `f53260db57e6f01bfac7a29e83f0091aeabf94aab566c3d641e89176298b980c`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/20e639b5398aa99f/results.jsonl`, dossier generated at `runs/dossiers/dossier-20e639b5398aa99f-f53260db57e6f01bfac7a29e83f0091aeabf94aab566c3d641e89176298b980c.json`.

## Cycle 10 Findings (Offset 152, Limit 16)

1.  **Run ID:** `5335bf7a8591a569`
2.  **Top Candidate:** `f(x0,f(x0,x1)) = f(x1,x1)` (Axiom ID: `6a25fa90a69534cb71dc7086a7af1bfd3627cf2aaafb62eb8b4761b3e6ade38d`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/5335bf7a8591a569/results.jsonl`, dossier generated at `runs/dossiers/dossier-5335bf7a8591a569-6a25fa90a69534cb71dc7086a7af1bfd3627cf2aaafb62eb8b4761b3e6ade38d.json`.

## Cycle 11 Findings (Offset 168, Limit 16)

1.  **Run ID:** `c6e810b3672e2d33`
2.  **Top Candidate:** `f(x0,f(x1,x0)) = f(x0,x0)` (Axiom ID: `10ebf8ac6e87f0aab70d7d97c1a9012cce436c2a0026b187fc51fd2fda1e69d2`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/c6e810b3672e2d33/results.jsonl`, dossier generated at `runs/dossiers/dossier-c6e810b3672e2d33-10ebf8ac6e87f0aab70d7d97c1a9012cce436c2a0026b187fc51fd2fda1e69d2.json`.

## Cycle 12 Findings (Offset 184, Limit 16)

1.  **Run ID:** `a306fc527cc5fc27`
2.  **Top Candidate:** `f(x0,f(x1,x0)) = f(f(x1,x1),x0)` (Axiom ID: `1c4ea30e050c9258cde6025cb3a94b24795e411c2f119eb19c827b7cd2b549ce`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/a306fc527cc5fc27/results.jsonl`, dossier generated at `runs/dossiers/dossier-a306fc527cc5fc27-1c4ea30e050c9258cde6025cb3a94b24795e411c2f119eb19c827b7cd2b549ce.json`.

## Cycle 13 Findings (Offset 200, Limit 16)

1.  **Run ID:** `96609a99addfb143`
2.  **Top Candidate:** `f(x0,f(x1,x1)) = f(x0,x0)` (Axiom ID: `518f341d704799bcddd4b34182f40b696e52f0223f62a46abd692407067f1f26`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/96609a99addfb143/results.jsonl`, dossier generated at `runs/dossiers/dossier-96609a99addfb143-518f341d704799bcddd4b34182f40b696e52f0223f62a46abd692407067f1f26.json`.

## Cycle 14 Findings (Offset 216, Limit 16)

1.  **Run ID:** `60c5fe9d715df4b6`
2.  **Top Candidate:** `f(x1,f(x0,x0)) = f(x1,x0)` (Axiom ID: `8d001d577ae8a5f83f91792fe0429bab94b2746bfcc0803f0afa200d38236665`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/60c5fe9d715df4b6/results.jsonl`, dossier generated at `runs/dossiers/dossier-60c5fe9d715df4b6-8d001d577ae8a5f83f91792fe0429bab94b2746bfcc0803f0afa200d38236665.json`.

## Cycle 15 Findings (Offset 232, Limit 16)

1.  **Run ID:** `e1192a3fdb388c64`
2.  **Top Candidate:** `f(x1,f(x0,x1)) = f(x1,x1)` (Axiom ID: `51e05d83ac3b2f6fc8325d519d471d66ee55097f4060173bc0789799ca76cd4a`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/e1192a3fdb388c64/results.jsonl`, dossier generated at `runs/dossiers/dossier-e1192a3fdb388c64-51e05d83ac3b2f6fc8325d519d471d66ee55097f4060173bc0789799ca76cd4a.json`.

## Cycle 16 Findings (Offset 248, Limit 16)

1.  **Run ID:** `d0e074ff9c0cfe7d`
2.  **Top Candidate:** `f(x1,f(x0,x1)) = f(f(x1,x1),x0)` (Axiom ID: `1019dc47f5660153547a0fbb529a48f7a2432d7d37729b9a59a78033f7c93a4d`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/d0e074ff9c0cfe7d/results.jsonl`, dossier generated at `runs/dossiers/dossier-d0e074ff9c0cfe7d-1019dc47f5660153547a0fbb529a48f7a2432d7d37729b9a59a78033f7c93a4d.json`.

## Cycle 17 Findings (Offset 264, Limit 16)

1.  **Run ID:** `2cf7a39c5eb0a9c4`
2.  **Top Candidate:** `f(x1,f(x1,x0)) = f(x0,x0)` (Axiom ID: `300531b4c4dbc458e60fa5bc6607739e167f8b67f71c13d222ad4742423a54ec`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/2cf7a39c5eb0a9c4/results.jsonl`, dossier generated at `runs/dossiers/dossier-2cf7a39c5eb0a9c4-300531b4c4dbc458e60fa5bc6607739e167f8b67f71c13d222ad4742423a54ec.json`.

## Cycle 18 Findings (Offset 280, Limit 16)

1.  **Run ID:** `3eebeba1941547d5`
2.  **Top Candidate:** `f(x1,f(x1,x1)) = f(x0,x0)` (Axiom ID: `661f77907506efb64ac59ee34ab6c4d721e8cd60f9192915ed990c4cbf2a6f9d`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/3eebeba1941547d5/results.jsonl`, dossier generated at `runs/dossiers/dossier-3eebeba1941547d5-661f77907506efb64ac59ee34ab6c4d721e8cd60f9192915ed990c4cbf2a6f9d.json`.

## Cycle 19 Findings (Offset 296, Limit 16)

1.  **Run ID:** `454d944a6ae2d99f`
2.  **Top Candidate:** `f(x1,f(x1,x1)) = f(f(x1,x1),x1)` (Axiom ID: `df870aa56702ae411e5c3c44eccf665a7940e7f67b2936869cd59ac9ade2810c`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/454d944a6ae2d99f/results.jsonl`, dossier generated at `runs/dossiers/dossier-454d944a6ae2d99f-df870aa56702ae411e5c3c44eccf665a7940e7f67b2936869cd59ac9ade2810c.json`.

## Cycle 20 Findings (Offset 312, Limit 16)

1.  **Run ID:** `c823da22619e07c3`
2.  **Top Candidate:** `f(f(x0,x0),x0) = f(x1,x1)` (Axiom ID: `78b11eab5a05be5d6872f09571eca006c0a87434823fae8b970346e2d060653e`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/c823da22619e07c3/results.jsonl`, dossier generated at `runs/dossiers/dossier-c823da22619e07c3-78b11eab5a05be5d6872f09571eca006c0a87434823fae8b970346e2d060653e.json`.

## Cycle 21 Findings (Offset 328, Limit 16)

1.  **Run ID:** `dd88a6cdaabb8d75`
2.  **Top Candidate:** `f(f(x0,x0),x1) = f(x0,x1)` (Axiom ID: `de2440d214e3ff4315dbfb7d70439cea438ec690e29b770c81a609928962fb4a`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/dd88a6cdaabb8d75/results.jsonl`, dossier generated at `runs/dossiers/dossier-dd88a6cdaabb8d75-de2440d214e3ff4315dbfb7d70439cea438ec690e29b770c81a609928962fb4a.json`.

## Cycle 22 Findings (Offset 344, Limit 16)

1.  **Run ID:** `c3ed37cc82ecd89d`
2.  **Top Candidate:** `f(f(x0,x1),x0) = f(x0,x0)` (Axiom ID: `2ab49fd87277273f4c203e58b3c52f4dbb707094c2c087f38194e47705cf0b32`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/c3ed37cc82ecd89d/results.jsonl`, dossier generated at `runs/dossiers/dossier-c3ed37cc82ecd89d-2ab49fd87277273f4c203e58b3c52f4dbb707094c2c087f38194e47705cf0b32.json`.

## Cycle 23 Findings (Offset 360, Limit 16)

1.  **Run ID:** `07736fdbf22d18b6`
2.  **Top Candidate:** `f(f(x0,x1),x0) = f(f(x0,x0),x0)` (Axiom ID: `0f3825907874c405dc4c4e40c71b7161f912f81347a2490359cb478c0f796fc3`).
3.  **Findings:** The top candidate was flagged as "nontrivial" and its implication signature shows "counterexample" for all standard properties (associativity, etc.).
4.  **Artifacts:** Results saved to `runs/07736fdbf22d18b6/results.jsonl`, dossier generated at `runs/dossiers/dossier-07736fdbf22d18b6-0f3825907874c405dc4c4e40c71b7161f912f81347a2490359cb478c0f796fc3.json`.

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
