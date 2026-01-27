from __future__ import annotations

import re
from typing import Any, Dict

_CITATION_PATTERN = re.compile(r"\[[^\]]+\]")


def validate_dossier_citations(dossier: Dict[str, Any]) -> None:
    facts = dossier.get("facts")
    if not isinstance(facts, list):
        raise ValueError("Dossier facts must be a list.")
    for fact in facts:
        if not isinstance(fact, dict) or not fact.get("source"):
            raise ValueError("Dossier facts must include citation sources.")

    derived = dossier.get("derived_laws")
    if not isinstance(derived, list):
        raise ValueError("Dossier derived_laws must be a list.")
    for fact in derived:
        if not isinstance(fact, dict) or not fact.get("source"):
            raise ValueError("Dossier derived_laws must include citation sources.")

    narrative = dossier.get("narrative")
    if not isinstance(narrative, list):
        raise ValueError("Dossier narrative must be a list.")
    for line in narrative:
        if not isinstance(line, str) or not _CITATION_PATTERN.search(line):
            raise ValueError("Dossier narrative lines must include citations.")
