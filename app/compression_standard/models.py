"""
Modèles de données pour la compression standard.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SectionNode:
    """
    Représente une section logique du document.
    """
    id: str
    title: str
    level: int
    start_line: int
    end_line: int
    text: str
    section_type: str
    path: List[str] = field(default_factory=list)
    children: List["SectionNode"] = field(default_factory=list)
    meta: Dict[str, object] = field(default_factory=dict)

    @property
    def approx_tokens(self) -> int:
        from .utils import approximate_tokens
        return approximate_tokens(self.text)


@dataclass
class Packet:
    """
    Représente un paquet de sections consécutives.
    """
    id: str
    nodes: List[SectionNode]
    total_tokens: int
    section_types: List[str]
    titles: List[str]
    context_ribbon: Dict[str, object]

    @property
    def text(self) -> str:
        parts = []
        for node in self.nodes:
            path = " > ".join(node.path) if node.path else node.title
            parts.append(f"### PATH: {path}\n{node.text.strip()}")
        return "\n\n".join(parts)
