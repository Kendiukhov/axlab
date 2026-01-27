from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    spec: dict
    battery_config: dict
    manifest_digest: str
    results_digest: str


@dataclass(frozen=True)
class AxiomRecord:
    run_id: str
    axiom_id: str
    left_term: str
    right_term: str
    symmetry_class: str


@dataclass(frozen=True)
class ModelRecord:
    run_id: str
    axiom_id: str
    size: int
    status: str
    fingerprint: Optional[str]
    candidates: int
    elapsed_seconds: float


@dataclass(frozen=True)
class ImplicationRecord:
    run_id: str
    axiom_id: str
    theory: str
    status: str
    checked_max_size: int
    counterexample_size: Optional[int]
    counterexample_fingerprint: Optional[str]
    proof_status: Optional[str]
    proof_elapsed_seconds: Optional[float]
    proof_steps: Optional[list[dict[str, str]]]


@dataclass(frozen=True)
class MetricRecord:
    run_id: str
    axiom_id: str
    name: str
    value: Optional[float]
    value_json: Optional[str]


@dataclass(frozen=True)
class NoteRecord:
    note_id: int
    run_id: str
    axiom_id: str
    body: str
    created_at: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _artifact_path(root: Path, digest: str) -> Path:
    return root / "artifacts" / digest[:2] / digest


def _metric_payload(value: Any) -> tuple[Optional[float], Optional[str]]:
    if value is None:
        return None, None
    if isinstance(value, bool):
        return 1.0 if value else 0.0, None
    if isinstance(value, (int, float)):
        return float(value), None
    return None, _stable_json(value)


def _parse_metric_value(value: Optional[float], value_json: Optional[str]) -> Any:
    if value_json is not None:
        return json.loads(value_json)
    return value


def _serialize_proof_steps(steps: Optional[list[dict[str, str]]]) -> Optional[str]:
    if steps is None:
        return None
    return _stable_json(steps)


def _deserialize_proof_steps(payload: Optional[str]) -> Optional[list[dict[str, str]]]:
    if payload is None:
        return None
    return json.loads(payload)


class ArtifactStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "artifacts").mkdir(exist_ok=True)
        self.db_path = self.root / "store.db"
        self._init_db()

    def _init_db(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        schema = schema_path.read_text(encoding="utf-8")
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)

    def write_bytes(self, kind: str, data: bytes) -> str:
        digest = _digest_bytes(data)
        artifact_path = _artifact_path(self.root, digest)
        if not artifact_path.exists():
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_bytes(data)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO artifacts(digest, kind, size, created_at) VALUES (?, ?, ?, ?)",
                (digest, kind, len(data), _utc_now()),
            )
        return digest

    def write_json(self, kind: str, data: Any) -> str:
        payload = _stable_json(data).encode("utf-8")
        return self.write_bytes(kind, payload)

    def read_bytes(self, digest: str) -> bytes:
        return _artifact_path(self.root, digest).read_bytes()

    def read_json(self, digest: str) -> Any:
        return json.loads(self.read_bytes(digest).decode("utf-8"))

    def record_run(
        self,
        run_id: str,
        spec: dict,
        battery_config: dict,
        manifest_digest: str,
        results_digest: str,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO runs(run_id, created_at, spec_json, battery_config_json, manifest_digest, results_digest)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    _utc_now(),
                    _stable_json(spec),
                    _stable_json(battery_config),
                    manifest_digest,
                    results_digest,
                ),
            )

    def load_run(self, run_id: str) -> Optional[RunRecord]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT spec_json, battery_config_json, manifest_digest, results_digest FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        spec_json, config_json, manifest_digest, results_digest = row
        return RunRecord(
            run_id=run_id,
            spec=json.loads(spec_json),
            battery_config=json.loads(config_json),
            manifest_digest=manifest_digest,
            results_digest=results_digest,
        )

    def record_axiom(
        self,
        run_id: str,
        axiom_id: str,
        left_term: str,
        right_term: str,
        symmetry_class: str,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO axioms(run_id, axiom_id, left_term, right_term, symmetry_class, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, axiom_id, left_term, right_term, symmetry_class, _utc_now()),
            )

    def load_axiom(self, run_id: str, axiom_id: str) -> Optional[AxiomRecord]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT left_term, right_term, symmetry_class FROM axioms WHERE run_id = ? AND axiom_id = ?",
                (run_id, axiom_id),
            ).fetchone()
        if row is None:
            return None
        left_term, right_term, symmetry_class = row
        return AxiomRecord(
            run_id=run_id,
            axiom_id=axiom_id,
            left_term=left_term,
            right_term=right_term,
            symmetry_class=symmetry_class,
        )

    def list_axioms(self, run_id: str) -> list[AxiomRecord]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT axiom_id, left_term, right_term, symmetry_class FROM axioms WHERE run_id = ?",
                (run_id,),
            ).fetchall()
        return [
            AxiomRecord(
                run_id=run_id,
                axiom_id=axiom_id,
                left_term=left_term,
                right_term=right_term,
                symmetry_class=symmetry_class,
            )
            for axiom_id, left_term, right_term, symmetry_class in rows
        ]

    def lookup_axiom_by_symmetry(self, symmetry_class: str) -> Optional[AxiomRecord]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT run_id, axiom_id, left_term, right_term, symmetry_class"
                " FROM axioms WHERE symmetry_class = ? ORDER BY created_at LIMIT 1",
                (symmetry_class,),
            ).fetchone()
        if row is None:
            return None
        run_id, axiom_id, left_term, right_term, symmetry = row
        return AxiomRecord(
            run_id=run_id,
            axiom_id=axiom_id,
            left_term=left_term,
            right_term=right_term,
            symmetry_class=symmetry,
        )

    def axiom_symmetry_exists(self, symmetry_class: str) -> bool:
        return self.lookup_axiom_by_symmetry(symmetry_class) is not None

    def record_models(self, run_id: str, axiom_id: str, models: list[ModelRecord]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO models(run_id, axiom_id, size, status, fingerprint, candidates, elapsed_seconds, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        run_id,
                        axiom_id,
                        record.size,
                        record.status,
                        record.fingerprint,
                        record.candidates,
                        record.elapsed_seconds,
                        _utc_now(),
                    )
                    for record in models
                ],
            )

    def load_models(self, run_id: str, axiom_id: str) -> list[ModelRecord]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT size, status, fingerprint, candidates, elapsed_seconds"
                " FROM models WHERE run_id = ? AND axiom_id = ? ORDER BY size",
                (run_id, axiom_id),
            ).fetchall()
        return [
            ModelRecord(
                run_id=run_id,
                axiom_id=axiom_id,
                size=size,
                status=status,
                fingerprint=fingerprint,
                candidates=candidates,
                elapsed_seconds=elapsed_seconds,
            )
            for (size, status, fingerprint, candidates, elapsed_seconds) in rows
        ]

    def record_implications(
        self, run_id: str, axiom_id: str, implications: list[ImplicationRecord]
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO implications(run_id, axiom_id, theory, status, checked_max_size,"
                " counterexample_size, counterexample_fingerprint, proof_status, proof_elapsed_seconds, proof_steps_json, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        run_id,
                        axiom_id,
                        record.theory,
                        record.status,
                        record.checked_max_size,
                        record.counterexample_size,
                        record.counterexample_fingerprint,
                        record.proof_status,
                        record.proof_elapsed_seconds,
                        _serialize_proof_steps(record.proof_steps),
                        _utc_now(),
                    )
                    for record in implications
                ],
            )

    def load_implications(self, run_id: str, axiom_id: str) -> list[ImplicationRecord]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT theory, status, checked_max_size, counterexample_size, counterexample_fingerprint,"
                " proof_status, proof_elapsed_seconds, proof_steps_json"
                " FROM implications WHERE run_id = ? AND axiom_id = ? ORDER BY theory",
                (run_id, axiom_id),
            ).fetchall()
        return [
            ImplicationRecord(
                run_id=run_id,
                axiom_id=axiom_id,
                theory=theory,
                status=status,
                checked_max_size=checked_max_size,
                counterexample_size=counterexample_size,
                counterexample_fingerprint=counterexample_fingerprint,
                proof_status=proof_status,
                proof_elapsed_seconds=proof_elapsed_seconds,
                proof_steps=_deserialize_proof_steps(proof_steps_json),
            )
            for (
                theory,
                status,
                checked_max_size,
                counterexample_size,
                counterexample_fingerprint,
                proof_status,
                proof_elapsed_seconds,
                proof_steps_json,
            ) in rows
        ]

    def record_metrics(self, run_id: str, axiom_id: str, metrics: dict[str, Any]) -> None:
        rows = []
        for name, value in metrics.items():
            numeric, payload = _metric_payload(value)
            rows.append((run_id, axiom_id, name, numeric, payload, _utc_now()))
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO metrics(run_id, axiom_id, name, value, value_json, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )

    def load_metrics(self, run_id: str, axiom_id: str) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT name, value, value_json FROM metrics WHERE run_id = ? AND axiom_id = ?",
                (run_id, axiom_id),
            ).fetchall()
        return {name: _parse_metric_value(value, value_json) for name, value, value_json in rows}

    def add_note(self, run_id: str, axiom_id: str, body: str) -> NoteRecord:
        created_at = _utc_now()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO notes(run_id, axiom_id, body, created_at) VALUES (?, ?, ?, ?)",
                (run_id, axiom_id, body, created_at),
            )
            note_id = int(cursor.lastrowid)
        return NoteRecord(
            note_id=note_id,
            run_id=run_id,
            axiom_id=axiom_id,
            body=body,
            created_at=created_at,
        )

    def load_notes(self, run_id: str, axiom_id: str) -> list[NoteRecord]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT note_id, body, created_at FROM notes WHERE run_id = ? AND axiom_id = ? ORDER BY note_id",
                (run_id, axiom_id),
            ).fetchall()
        return [
            NoteRecord(
                note_id=note_id,
                run_id=run_id,
                axiom_id=axiom_id,
                body=body,
                created_at=created_at,
            )
            for (note_id, body, created_at) in rows
        ]
