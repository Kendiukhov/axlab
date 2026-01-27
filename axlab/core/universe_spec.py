from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class OperationSpec:
    name: str
    arity: int
    commutative: bool = False


@dataclass(frozen=True)
class UniverseSpec:
    version: str
    logic: str
    operations: List[OperationSpec]
    max_vars: int
    max_term_size: int

    def op_map(self) -> Dict[str, OperationSpec]:
        return {op.name: op for op in self.operations}

    def validate(self) -> None:
        if self.logic != "equational":
            raise ValueError("Only equational logic is supported.")
        if self.max_vars < 1:
            raise ValueError("max_vars must be >= 1.")
        if self.max_term_size < 1:
            raise ValueError("max_term_size must be >= 1.")
        seen = set()
        for op in self.operations:
            if op.name in seen:
                raise ValueError(f"Duplicate operation name: {op.name}")
            seen.add(op.name)
            if op.arity not in (1, 2):
                raise ValueError(f"Unsupported arity for {op.name}: {op.arity}")

    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "logic": self.logic,
            "operations": [
                {"name": op.name, "arity": op.arity, "commutative": op.commutative}
                for op in self.operations
            ],
            "max_vars": self.max_vars,
            "max_term_size": self.max_term_size,
        }

    @staticmethod
    def from_dict(data: Dict) -> "UniverseSpec":
        ops = [
            OperationSpec(
                name=op["name"],
                arity=int(op["arity"]),
                commutative=bool(op.get("commutative", False)),
            )
            for op in data["operations"]
        ]
        spec = UniverseSpec(
            version=str(data.get("version", "v0")),
            logic=str(data["logic"]),
            operations=ops,
            max_vars=int(data["max_vars"]),
            max_term_size=int(data["max_term_size"]),
        )
        spec.validate()
        return spec

    @staticmethod
    def from_json(text: str) -> "UniverseSpec":
        return UniverseSpec.from_dict(json.loads(text))

    @staticmethod
    def load_json(path: str) -> "UniverseSpec":
        with open(path, "r", encoding="utf-8") as handle:
            return UniverseSpec.from_json(handle.read())

    def variable_names(self) -> Iterable[str]:
        for idx in range(self.max_vars):
            yield f"x{idx}"
