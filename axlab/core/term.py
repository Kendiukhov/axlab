from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class Term:
    kind: str
    value: str
    args: Tuple["Term", ...] = ()

    @staticmethod
    def var(name: str) -> "Term":
        return Term("var", name, ())

    @staticmethod
    def op(name: str, args: Iterable["Term"]) -> "Term":
        return Term("op", name, tuple(args))

    def size(self) -> int:
        if self.kind == "var":
            return 1
        return 1 + sum(arg.size() for arg in self.args)

    def vars(self) -> Tuple[str, ...]:
        if self.kind == "var":
            return (self.value,)
        names = []
        for arg in self.args:
            names.extend(arg.vars())
        return tuple(names)

    def depth(self) -> int:
        if self.kind == "var":
            return 1
        return 1 + max(arg.depth() for arg in self.args)

    def serialize(self) -> str:
        if self.kind == "var":
            return self.value
        inner = ",".join(arg.serialize() for arg in self.args)
        return f"{self.value}({inner})"

    @staticmethod
    def parse(text: str) -> "Term":
        text = text.strip()
        if not text:
            raise ValueError("Cannot parse empty term.")

        def parse_name(source: str, idx: int) -> tuple[str, int]:
            start = idx
            while idx < len(source) and source[idx] not in "(),":
                idx += 1
            if start == idx:
                raise ValueError(f"Expected name at position {idx}.")
            return source[start:idx], idx

        def parse_term(source: str, idx: int) -> tuple["Term", int]:
            name, idx = parse_name(source, idx)
            if idx < len(source) and source[idx] == "(":
                idx += 1
                args = []
                if idx >= len(source):
                    raise ValueError("Unclosed argument list.")
                while True:
                    arg, idx = parse_term(source, idx)
                    args.append(arg)
                    if idx >= len(source):
                        raise ValueError("Unclosed argument list.")
                    if source[idx] == ",":
                        idx += 1
                        continue
                    if source[idx] == ")":
                        idx += 1
                        break
                    raise ValueError(f"Unexpected character '{source[idx]}' at {idx}.")
                return Term.op(name, args), idx
            return Term.var(name), idx

        term, idx = parse_term(text, 0)
        if idx != len(text):
            raise ValueError(f"Unexpected trailing text at {idx}.")
        return term
