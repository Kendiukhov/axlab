from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from axlab.core.canonicalization import canonicalize_equation
from axlab.core.term import Term
from axlab.core.universe_spec import UniverseSpec
from axlab.engines.model_finder.interface import ModelSearchConfig
from axlab.engines.model_finder.naive import find_model_with_constraints
from axlab.pipeline.battery import BatteryConfig, BatteryResult
from axlab.pipeline.implications import ImplicationProbe, library_for_spec


@dataclass(frozen=True)
class InterpretationConfig:
    max_model_size: int = 3
    max_model_candidates: int = 10_000
    max_model_seconds: float = 1.0
    neighbor_count: int = 3

    @classmethod
    def from_battery_config(cls, config: BatteryConfig) -> "InterpretationConfig":
        return cls(
            max_model_size=config.max_model_size,
            max_model_candidates=config.max_model_candidates,
            max_model_seconds=config.max_model_seconds,
        )

    def override(self, payload: Dict[str, Any]) -> "InterpretationConfig":
        return InterpretationConfig(
            max_model_size=int(payload.get("max_model_size", self.max_model_size)),
            max_model_candidates=int(payload.get("max_model_candidates", self.max_model_candidates)),
            max_model_seconds=float(payload.get("max_model_seconds", self.max_model_seconds)),
            neighbor_count=int(payload.get("neighbor_count", self.neighbor_count)),
        )


@dataclass(frozen=True)
class PropertyCheck:
    name: str
    status: str
    counterexample_size: Optional[int]
    counterexample_fingerprint: Optional[str]
    proof_status: Optional[str]
    proof_steps: Optional[List[Dict[str, str]]]


@dataclass(frozen=True)
class BenchmarkIdentityResult:
    name: str
    left: str
    right: str
    status: str
    counterexample_size: Optional[int]
    counterexample_fingerprint: Optional[str]


@dataclass(frozen=True)
class PrettyModel:
    size: int
    fingerprint: str
    lines: List[str]


@dataclass(frozen=True)
class TranslationCandidate:
    theory: str
    axiom_implies: str
    theory_implies: str
    status: str
    counterexample_size: Optional[int]
    counterexample_fingerprint: Optional[str]


@dataclass(frozen=True)
class NearestNeighbor:
    axiom_id: str
    left: str
    right: str
    distance: float
    shared_confirmed: List[str]


@dataclass(frozen=True)
class Fact:
    statement: str
    source: str


@dataclass(frozen=True)
class TheoryDossier:
    axiom: Dict[str, str]
    canonical_axiom: Dict[str, str]
    minimal_basis: List[Dict[str, str]]
    features: Dict[str, Any]
    degeneracy: Dict[str, Any]
    model_spectrum: List[Dict[str, Any]]
    smallest_model_size: Optional[int]
    model_pretty: List[PrettyModel]
    properties: List[PropertyCheck]
    benchmark_identities: List[BenchmarkIdentityResult]
    derived_laws: List[Fact]
    translations: List[TranslationCandidate]
    nearest_neighbors: List[NearestNeighbor]
    facts: List[Fact]
    narrative: List[str]
    open_questions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "axiom": self.axiom,
            "canonical_axiom": self.canonical_axiom,
            "minimal_basis": self.minimal_basis,
            "features": self.features,
            "degeneracy": self.degeneracy,
            "model_spectrum": self.model_spectrum,
            "smallest_model_size": self.smallest_model_size,
            "model_pretty": [model.__dict__ for model in self.model_pretty],
            "properties": [prop.__dict__ for prop in self.properties],
            "benchmark_identities": [bench.__dict__ for bench in self.benchmark_identities],
            "derived_laws": [fact.__dict__ for fact in self.derived_laws],
            "translations": [candidate.__dict__ for candidate in self.translations],
            "nearest_neighbors": [neighbor.__dict__ for neighbor in self.nearest_neighbors],
            "facts": [fact.__dict__ for fact in self.facts],
            "narrative": list(self.narrative),
            "open_questions": list(self.open_questions),
        }


def interpret_axiom(
    spec: UniverseSpec,
    axiom: Tuple[Term, Term],
    result: BatteryResult,
    config: InterpretationConfig,
    peer_results: Optional[
        List[Tuple[str, Tuple[Term, Term], BatteryResult]]
    ] = None,
) -> TheoryDossier:
    left, right = axiom
    canon_left, canon_right = canonicalize_equation(left, right, spec)
    canonical_axiom = {"left": canon_left.serialize(), "right": canon_right.serialize()}
    minimal_basis = [canonical_axiom]

    properties = _properties_from_implications(result.implications)
    benchmark_identities = _run_benchmark_suite(spec, (canon_left, canon_right), config)
    model_pretty = _pretty_models(spec, result.model_spectrum)
    translations = _translation_search(spec, (canon_left, canon_right), result.implications, config)
    nearest_neighbors = _nearest_neighbors(
        result,
        peer_results,
        config.neighbor_count,
    )
    derived_laws = _derived_laws(properties, benchmark_identities)
    facts = _build_facts(result, properties, benchmark_identities, translations, nearest_neighbors)
    narrative = _compile_narrative(canonical_axiom, result, properties, benchmark_identities, facts)
    open_questions = _open_questions(properties, benchmark_identities, translations)

    return TheoryDossier(
        axiom={"left": left.serialize(), "right": right.serialize()},
        canonical_axiom=canonical_axiom,
        minimal_basis=minimal_basis,
        features=result.features.__dict__,
        degeneracy=result.degeneracy.__dict__,
        model_spectrum=[entry.__dict__ for entry in result.model_spectrum],
        smallest_model_size=result.smallest_model_size,
        model_pretty=model_pretty,
        properties=properties,
        benchmark_identities=benchmark_identities,
        derived_laws=derived_laws,
        translations=translations,
        nearest_neighbors=nearest_neighbors,
        facts=facts,
        narrative=narrative,
        open_questions=open_questions,
    )


def _properties_from_implications(implications: Sequence[ImplicationProbe]) -> List[PropertyCheck]:
    checks: List[PropertyCheck] = []
    for probe in implications:
        steps = None
        if probe.proof_steps is not None:
            steps = [
                {"rule": step.rule, "left": step.left, "right": step.right}
                for step in probe.proof_steps
            ]
        checks.append(
            PropertyCheck(
                name=probe.theory,
                status=probe.status,
                counterexample_size=probe.counterexample_size,
                counterexample_fingerprint=probe.counterexample_fingerprint,
                proof_status=probe.proof_status,
                proof_steps=steps,
            )
        )
    return checks


def _first_op_name(spec: UniverseSpec, arity: int) -> Optional[str]:
    for op in spec.operations:
        if op.arity == arity:
            return op.name
    return None


def _benchmark_identities(spec: UniverseSpec) -> List[Tuple[str, Term, Term]]:
    benchmarks: List[Tuple[str, Term, Term]] = []
    binary = _first_op_name(spec, 2)
    unary = _first_op_name(spec, 1)
    if binary:
        x0 = Term.var("x0")
        x1 = Term.var("x1")
        x2 = Term.var("x2")
        x3 = Term.var("x3")
        f = lambda *args: Term.op(binary, list(args))
        benchmarks.extend(
            [
                ("left_absorption", f(x0, f(x0, x1)), x0),
                ("right_absorption", f(f(x0, x1), x1), x1),
                ("left_distributive", f(x0, f(x1, x2)), f(f(x0, x1), f(x0, x2))),
                ("right_distributive", f(f(x0, x1), x2), f(f(x0, x2), f(x1, x2))),
                ("medial", f(f(x0, x1), f(x2, x3)), f(f(x0, x2), f(x1, x3))),
            ]
        )
    if unary:
        x0 = Term.var("x0")
        g = lambda arg: Term.op(unary, [arg])
        benchmarks.extend(
            [
                ("unary_idempotent", g(g(x0)), g(x0)),
                ("unary_involutive", g(g(x0)), x0),
            ]
        )
    return benchmarks


def _run_benchmark_suite(
    spec: UniverseSpec, axiom: Tuple[Term, Term], config: InterpretationConfig
) -> List[BenchmarkIdentityResult]:
    search_config = ModelSearchConfig(
        max_candidates=config.max_model_candidates,
        max_seconds=config.max_model_seconds,
    )
    results: List[BenchmarkIdentityResult] = []
    for name, left, right in _benchmark_identities(spec):
        status, counterexample_size, counterexample_fingerprint = _implication_status(
            spec, [axiom], (left, right), config.max_model_size, search_config
        )
        results.append(
            BenchmarkIdentityResult(
                name=name,
                left=left.serialize(),
                right=right.serialize(),
                status=status,
                counterexample_size=counterexample_size,
                counterexample_fingerprint=counterexample_fingerprint,
            )
        )
    return results


def _implication_status(
    spec: UniverseSpec,
    axioms: List[Tuple[Term, Term]],
    identity: Tuple[Term, Term],
    max_model_size: int,
    search_config: ModelSearchConfig,
) -> Tuple[str, Optional[int], Optional[str]]:
    counterexample_size = None
    counterexample_fingerprint = None
    cutoff = False
    for size in range(1, max_model_size + 1):
        result = find_model_with_constraints(
            spec,
            axioms,
            size,
            search_config,
            must_violate=identity,
        )
        if result.status == "found":
            counterexample_size = size
            counterexample_fingerprint = result.fingerprint
            break
        if result.status in ("timeout", "cutoff"):
            cutoff = True
    if counterexample_size is not None:
        return "counterexample", counterexample_size, counterexample_fingerprint
    if cutoff:
        return "inconclusive", None, None
    return "confirmed", None, None


def _pretty_models(spec: UniverseSpec, spectrum: Sequence[Any]) -> List[PrettyModel]:
    models: List[PrettyModel] = []
    for entry in spectrum:
        if entry.status != "found" or entry.fingerprint is None:
            continue
        models.append(_pretty_model_from_fingerprint(spec, entry.fingerprint))
    return models


def _pretty_model_from_fingerprint(spec: UniverseSpec, fingerprint: str) -> PrettyModel:
    parts = fingerprint.split(";")
    size = 0
    tables: Dict[str, List[int]] = {}
    for part in parts:
        if part.startswith("n="):
            size = int(part.split("=", 1)[1])
            continue
        if "=" not in part:
            continue
        name, payload = part.split("=", 1)
        if payload:
            tables[name] = [int(value) for value in payload.split(",")]
        else:
            tables[name] = []
    lines: List[str] = []
    for op in spec.operations:
        table = tables.get(op.name, [])
        lines.append(f"{op.name}:")
        if op.arity == 1:
            row = " ".join(str(value) for value in table)
            lines.append(f"  {row}")
        else:
            for row_idx in range(size):
                start = row_idx * size
                row = table[start : start + size]
                lines.append("  " + " ".join(str(value) for value in row))
    return PrettyModel(size=size, fingerprint=fingerprint, lines=lines)


def _translation_search(
    spec: UniverseSpec,
    axiom: Tuple[Term, Term],
    implications: Sequence[ImplicationProbe],
    config: InterpretationConfig,
) -> List[TranslationCandidate]:
    search_config = ModelSearchConfig(
        max_candidates=config.max_model_candidates,
        max_seconds=config.max_model_seconds,
    )
    implication_map = {probe.theory: probe for probe in implications}
    candidates: List[TranslationCandidate] = []
    for theory in library_for_spec(spec):
        probe = implication_map.get(theory.name)
        if probe is None:
            continue
        axiom_implies = probe.status
        status = "inconclusive"
        theory_implies = "inconclusive"
        counterexample_size = None
        counterexample_fingerprint = None
        if axiom_implies == "confirmed":
            theory_implies, counterexample_size, counterexample_fingerprint = _implication_status(
                spec,
                [(theory.left, theory.right)],
                axiom,
                config.max_model_size,
                search_config,
            )
            if theory_implies == "confirmed":
                status = "equivalent"
            elif theory_implies == "counterexample":
                status = "theory_stronger"
            else:
                status = "inconclusive"
        elif axiom_implies == "counterexample":
            status = "no_match"
        candidates.append(
            TranslationCandidate(
                theory=theory.name,
                axiom_implies=axiom_implies,
                theory_implies=theory_implies,
                status=status,
                counterexample_size=counterexample_size,
                counterexample_fingerprint=counterexample_fingerprint,
            )
        )
    return candidates


def _nearest_neighbors(
    result: BatteryResult,
    peer_results: Optional[List[Tuple[str, Tuple[Term, Term], BatteryResult]]],
    count: int,
) -> List[NearestNeighbor]:
    if not peer_results or count <= 0:
        return []
    target_sig = _implication_signature(result.implications)
    neighbors: List[NearestNeighbor] = []
    for axiom_id, (left, right), peer in peer_results:
        if peer is result:
            continue
        signature = _implication_signature(peer.implications)
        distance, shared_confirmed = _signature_distance(target_sig, signature)
        neighbors.append(
            NearestNeighbor(
                axiom_id=axiom_id,
                left=left.serialize(),
                right=right.serialize(),
                distance=distance,
                shared_confirmed=shared_confirmed,
            )
        )
    neighbors.sort(key=lambda item: (item.distance, item.axiom_id))
    return neighbors[:count]


def _implication_signature(implications: Sequence[ImplicationProbe]) -> Dict[str, int]:
    mapping = {"confirmed": 1, "counterexample": -1, "inconclusive": 0}
    return {probe.theory: mapping.get(probe.status, 0) for probe in implications}


def _signature_distance(
    target: Dict[str, int], candidate: Dict[str, int]
) -> Tuple[float, List[str]]:
    distance = 0.0
    shared_confirmed: List[str] = []
    for key in sorted(set(target) | set(candidate)):
        left = target.get(key, 0)
        right = candidate.get(key, 0)
        distance += abs(left - right)
        if left == 1 and right == 1:
            shared_confirmed.append(key)
    return distance, shared_confirmed


def _derived_laws(
    properties: Sequence[PropertyCheck], benchmarks: Sequence[BenchmarkIdentityResult]
) -> List[Fact]:
    facts: List[Fact] = []
    for prop in properties:
        if prop.status == "confirmed":
            facts.append(Fact(statement=f"{prop.name} confirmed", source=f"implication.{prop.name}"))
    for bench in benchmarks:
        if bench.status == "confirmed":
            facts.append(
                Fact(statement=f"{bench.name} identity holds", source=f"benchmark.{bench.name}")
            )
    return facts


def _build_facts(
    result: BatteryResult,
    properties: Sequence[PropertyCheck],
    benchmarks: Sequence[BenchmarkIdentityResult],
    translations: Sequence[TranslationCandidate],
    neighbors: Sequence[NearestNeighbor],
) -> List[Fact]:
    facts: List[Fact] = []
    if result.smallest_model_size is not None:
        facts.append(
            Fact(
                statement=f"smallest model size {result.smallest_model_size}",
                source="models.spectrum",
            )
        )
    for prop in properties:
        if prop.status == "confirmed":
            facts.append(Fact(statement=f"{prop.name} property confirmed", source=f"implication.{prop.name}"))
        elif prop.status == "counterexample":
            facts.append(
                Fact(statement=f"{prop.name} property refuted", source=f"implication.{prop.name}")
            )
    for bench in benchmarks:
        if bench.status == "confirmed":
            facts.append(
                Fact(statement=f"{bench.name} benchmark confirmed", source=f"benchmark.{bench.name}")
            )
    for candidate in translations:
        if candidate.status == "equivalent":
            facts.append(
                Fact(
                    statement=f"definitional equivalence with {candidate.theory}",
                    source=f"translation.{candidate.theory}",
                )
            )
    for neighbor in neighbors:
        facts.append(
            Fact(
                statement=f"nearest neighbor {neighbor.axiom_id} at distance {neighbor.distance}",
                source="neighbors.implication",
            )
        )
    return facts


def _compile_narrative(
    canonical_axiom: Dict[str, str],
    result: BatteryResult,
    properties: Sequence[PropertyCheck],
    benchmarks: Sequence[BenchmarkIdentityResult],
    facts: Sequence[Fact],
) -> List[str]:
    def _citation_list(prefix: str, names: Iterable[str]) -> str:
        return ", ".join(f"{prefix}.{name}" for name in sorted(set(names)))

    lines: List[str] = []
    lines.append(
        f"Canonical axiom: {canonical_axiom['left']} = {canonical_axiom['right']} [axiom]"
    )
    if result.smallest_model_size is not None:
        lines.append(
            f"Smallest model found at size {result.smallest_model_size} [models.spectrum]"
        )
    confirmed_props = [prop.name for prop in properties if prop.status == "confirmed"]
    refuted_props = [prop.name for prop in properties if prop.status == "counterexample"]
    if confirmed_props:
        citations = _citation_list("implication", confirmed_props)
        lines.append(
            "Confirmed properties: "
            + ", ".join(sorted(confirmed_props))
            + f" [{citations}]"
        )
    if refuted_props:
        citations = _citation_list("implication", refuted_props)
        lines.append(
            "Refuted properties: " + ", ".join(sorted(refuted_props)) + f" [{citations}]"
        )
    confirmed_bench = [bench.name for bench in benchmarks if bench.status == "confirmed"]
    if confirmed_bench:
        citations = _citation_list("benchmark", confirmed_bench)
        lines.append(
            "Benchmark identities satisfied: "
            + ", ".join(sorted(confirmed_bench))
            + f" [{citations}]"
        )
    if facts:
        lines.append(
            "Evidence summary: "
            + "; ".join(f"{fact.statement} [{fact.source}]" for fact in facts[:4])
        )
    return lines


def _open_questions(
    properties: Sequence[PropertyCheck],
    benchmarks: Sequence[BenchmarkIdentityResult],
    translations: Sequence[TranslationCandidate],
) -> List[str]:
    questions: List[str] = []
    for prop in properties:
        if prop.status == "inconclusive":
            questions.append(f"Resolve property {prop.name} with larger model search.")
    for bench in benchmarks:
        if bench.status == "inconclusive":
            questions.append(f"Resolve benchmark {bench.name} with larger model search.")
    for candidate in translations:
        if candidate.status == "inconclusive":
            questions.append(f"Check definitional equivalence with {candidate.theory}.")
    return questions
