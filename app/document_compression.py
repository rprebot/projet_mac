"""
Module de compression de documents juridiques longs.

Pipeline :
1. Parser le document en sections (SectionNode)
2. Découper en paquets (Packet) respectant un budget de tokens
3. Générer des prompts pour extraction intermédiaire par paquet
4. Générer un prompt final pour synthèse à partir des JSON extraits
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ============================================================
# Data structures
# ============================================================

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


# ============================================================
# Heuristics and constants
# ============================================================

SECTION_TYPE_PATTERNS: List[Tuple[str, List[re.Pattern[str]]]] = [
    (
        "header",
        [
            re.compile(r"\bPOUR\s*:", re.I),
            re.compile(r"\bCONTRE\s*:", re.I),
            re.compile(r"\bAPPELANT[E]?\b", re.I),
            re.compile(r"\bINTIM[ÉE]?\b", re.I),
        ],
    ),
    (
        "facts",
        [
            re.compile(r"\bLES FAITS\b", re.I),
            re.compile(r"\bRAPPEL DES FAITS\b", re.I),
            re.compile(r"\bEXPOS[ÉE] DES FAITS\b", re.I),
        ],
    ),
    (
        "procedure",
        [
            re.compile(r"\bLA PROC[ÉE]DURE\b", re.I),
            re.compile(r"\bRAPPEL DE LA PROC[ÉE]DURE\b", re.I),
            re.compile(r"\bPROC[ÉE]DURE\b", re.I),
        ],
    ),
    (
        "claims",
        [
            re.compile(r"\bPAR CES MOTIFS\b", re.I),
            re.compile(r"\bDISPOSITIF\b", re.I),
            re.compile(r"\bIL PLA[IÎ]T\b", re.I),
            re.compile(r"\bEN CONS[ÉE]QUENCE\b", re.I),
        ],
    ),
    (
        "discussion",
        [
            re.compile(r"\bDISCUSSION\b", re.I),
            re.compile(r"\bEN DROIT\b", re.I),
            re.compile(r"\bMOYENS\b", re.I),
            re.compile(r"\bARGUMENTAIRE\b", re.I),
        ],
    ),
]

HEADING_PATTERNS: List[Tuple[int, re.Pattern[str], str]] = [
    (1, re.compile(r"^\s*[IVXLCDM]+\s*[\.-]\s+.+$"), "roman"),
    (1, re.compile(r"^\s*[IVXLCDM]+\s*$"), "roman_only"),
    (2, re.compile(r"^\s*[A-Z]\s*-\s+.+$"), "alpha"),
    (3, re.compile(r"^\s*\d+\s*[-°\.)]\s+.+$"), "numeric"),
    (3, re.compile(r"^\s*GRIEF\s*\d+\s*:?\s*$", re.I), "grief"),
    (4, re.compile(r"^\s*[a-z]\)\s+.+$"), "subalpha"),
    (1, re.compile(r"^\s*[A-ZÉÈÀÙÂÊÎÔÛÇ'\-\s]{6,}\s*$"), "caps"),
]

ARTICLE_RE = re.compile(r"\b(article|articles)\s+[A-Z]?\s*\d+[\d\-\.]*\b", re.I)
CASELAW_RE = re.compile(
    r"\bCass\.\s*"
    r"(?:soc\.|civ\.|com\.|crim\.)?"
    r".{0,80}?"
    r"n[°º]\s*\d{2}-\d{2}\.\d{3}\b",
    re.I,
)
MONEY_RE = re.compile(r"\b\d{1,3}(?:[ .]\d{3})*(?:,\d{2})?\s*€")
DATE_RE = re.compile(
    r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\s+[a-zéûîôàè]+\s+\d{4})\b",
    re.I,
)

PERSON_ENTITY_PATTERNS: List[Tuple[str, re.Pattern[str], Optional[str], Optional[str]]] = [
    ("lawyer", re.compile(r"\bMa[iî]tre\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", re.I), "neutral", "lawyer"),
    ("person", re.compile(r"\b(?:Monsieur|Madame|M\.)\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", re.I), None, "person"),
    ("association", re.compile(r"\b(?:L[''])?ASSOCIATION\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", re.I), None, "organization"),
    ("societe", re.compile(r"\b(?:Soci[ée]t[ée]|SARL|SAS|SA|SCI)\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", re.I), None, "organization"),
    ("jurisdiction", re.compile(r"\b(?:Conseil de prud['']hommes|Cour d['']appel|Cour de cassation|Tribunal judiciaire)\b", re.I), "neutral", "institution"),
    ("occupational_physician", re.compile(r"\bm[ée]decin du travail\b", re.I), "neutral", "institutional_actor"),
]

ROLE_HINT_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bappelant[e]?\b", re.I), "appelant"),
    (re.compile(r"\bintim[ée]?\b", re.I), "intimé"),
    (re.compile(r"\bdemandeur\b", re.I), "demandeur"),
    (re.compile(r"\bd[ée]fendeur\b", re.I), "défendeur"),
    (re.compile(r"\bvice-pr[ée]sident[e]?\b", re.I), "vice-président"),
    (re.compile(r"\bpr[ée]sident[e]?\b", re.I), "président"),
    (re.compile(r"\btr[ée]sorier\b|\btr[ée]sori[èe]re\b", re.I), "trésorier"),
    (re.compile(r"\bresponsable des ressources humaines\b|\br[ée]f[ée]rente RH\b", re.I), "RH"),
    (re.compile(r"\bsalari[ée]\b", re.I), "salarié"),
    (re.compile(r"\bemployeur\b", re.I), "employeur"),
]

SIDE_HINT_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bappelant[e]?\b", re.I), "current_party"),
    (re.compile(r"\bintim[ée]?\b", re.I), "opposing_party"),
    (re.compile(r"\bdemandeur\b", re.I), "current_party"),
    (re.compile(r"\bd[ée]fendeur\b", re.I), "opposing_party"),
    (re.compile(r"\bemployeur\b", re.I), "current_party"),
    (re.compile(r"\bsalari[ée]\b", re.I), "opposing_party"),
]

ROLE_BLACKLIST_KINDS = {"institution", "institutional_actor"}
ROLE_WINDOW = 80
SIDE_WINDOW = 80


# ============================================================
# Utility functions
# ============================================================

def approximate_tokens(text: str) -> int:
    """Approximation simple (1 token pour 4 caractères)."""
    return max(1, math.ceil(len(text) / 4))


def normalize_space(text: str) -> str:
    text = text.replace("\u00A0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def clean_caselaw_match(s: str) -> str:
    s = clean_line(s)
    s = re.split(r"(?<=\d{2}-\d{2}\.\d{3})", s, maxsplit=1)[0]
    return s.strip(" .;,:)\"]»")


def guess_section_type(title: str, inherited: Optional[str] = None) -> str:
    for section_type, patterns in SECTION_TYPE_PATTERNS:
        if any(p.search(title) for p in patterns):
            return section_type
    if inherited:
        return inherited
    return "argument"


def heading_level_and_kind(line: str) -> Optional[Tuple[int, str]]:
    stripped = clean_line(line)
    if not stripped:
        return None
    if re.match(r"^(M|Mme|Mlle|Dr|Pr)\.\s+", stripped, re.I):
        return None
    for level, pattern, kind in HEADING_PATTERNS:
        if pattern.match(stripped):
            if kind == "caps" and len(stripped.split()) > 12:
                return None
            return level, kind
    return None


def split_lines(text: str) -> List[str]:
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def extract_header_registry(text: str) -> Dict[str, object]:
    normalized = normalize_space(text)
    registry = {
        "document_view": None,
        "parties": [],
        "by_name": {},
    }
    if re.search(r"\bCONCLUSIONS D['']APPELANT\b", normalized, re.I):
        registry["document_view"] = "appelant"
    elif re.search(r"\bCONCLUSIONS D['']INTIM[ÉE]?\b", normalized, re.I):
        registry["document_view"] = "intimé"

    header_text = normalized
    cut_markers = [
        r"\bI[\.\-]\s+LES FAITS\b",
        r"\bLES FAITS\b",
        r"\bRAPPEL DES FAITS\b",
        r"\bDISCUSSION\b",
    ]
    for marker in cut_markers:
        m = re.search(marker, header_text, re.I)
        if m:
            header_text = header_text[:m.start()]
            break

    pour_match = re.search(r"\bPOUR\s*:\s*(.*?)(?=\bCONTRE\s*:|$)", header_text, re.I | re.S)
    contre_match = re.search(r"\bCONTRE\s*:\s*(.*?)(?=$)", header_text, re.I | re.S)

    blocks = []
    if pour_match:
        blocks.append(("pour", pour_match.group(1)))
    if contre_match:
        blocks.append(("contre", contre_match.group(1)))

    for label, block in blocks:
        party_name = None
        party_kind = None
        procedural_role = None
        side = None
        lawyer = None

        m_org = re.search(r"\b(?:L[''])?ASSOCIATION\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", block, re.I)
        m_person = re.search(r"\b(?:Monsieur|Madame|M\.)\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", block, re.I)

        if m_org:
            party_name = clean_line(m_org.group(0))
            party_name = re.sub(r"^(?:L[''])?ASSOCIATION\b", "Association", party_name, flags=re.I)
            party_kind = "organization"
        elif m_person:
            party_name = clean_line(m_person.group(0))
            party_kind = "person"

        if re.search(r"\bAPPELANT[E]?\b", block, re.I):
            procedural_role = "appelant"
        elif re.search(r"\bINTIM[ÉE]?\b", block, re.I):
            procedural_role = "intimé"
        elif re.search(r"\bDEMANDEUR\b", block, re.I):
            procedural_role = "demandeur"
        elif re.search(r"\bD[ÉE]FENDEUR\b", block, re.I):
            procedural_role = "défendeur"

        if procedural_role == "appelant":
            side = "current_party" if registry["document_view"] == "appelant" else "opposing_party"
        elif procedural_role == "intimé":
            side = "current_party" if registry["document_view"] == "intimé" else "opposing_party"
        elif label == "pour":
            side = "current_party"
        elif label == "contre":
            side = "opposing_party"

        m_lawyer = re.search(r"\bMa[iî]tre\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", block, re.I)
        if m_lawyer:
            lawyer = clean_line(m_lawyer.group(0))

        if party_name:
            entry = {
                "name": party_name,
                "kind": party_kind,
                "procedural_role": procedural_role,
                "side": side,
                "lawyer": lawyer,
            }
            registry["parties"].append(entry)
            registry["by_name"][party_name.lower()] = entry

            if lawyer:
                registry["by_name"][lawyer.lower()] = {
                    "name": lawyer,
                    "kind": "lawyer",
                    "procedural_role": procedural_role,
                    "side": side,
                    "represents": party_name,
                }

    return registry


def canonicalize_entity_against_registry(entity: Dict[str, Optional[str]], header_registry: Dict[str, object]):
    by_name = header_registry.get("by_name", {})
    name = entity["name"]
    low = name.lower()

    if low in by_name:
        ref = by_name[low]
        if ref.get("side"):
            entity["side"] = ref["side"]
        if ref.get("procedural_role"):
            entity["role"] = ref["procedural_role"]
        entity["canonical_name"] = ref.get("name")
        return entity

    for ref_name, ref in by_name.items():
        if entity["kind"] != ref.get("kind"):
            continue
        entity_tokens = re.findall(r"\[[^\]]+\]", low)
        ref_tokens = re.findall(r"\[[^\]]+\]", ref_name)
        if entity_tokens and ref_tokens and set(entity_tokens).issubset(set(ref_tokens)):
            if ref.get("side"):
                entity["side"] = ref["side"]
            if ref.get("procedural_role"):
                entity["role"] = ref["procedural_role"]
            entity["canonical_name"] = ref.get("name")
            return entity

    return entity


def dedupe_entities(entities: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    seen: Dict[Tuple[str, str], Dict[str, Optional[str]]] = {}
    for ent in entities:
        key = (ent["name"].lower(), ent.get("kind") or "")
        if key not in seen:
            seen[key] = dict(ent)
            continue
        existing = seen[key]
        if not existing.get("role") and ent.get("role"):
            existing["role"] = ent["role"]
        if not existing.get("side") and ent.get("side"):
            existing["side"] = ent["side"]
    return list(seen.values())


def clean_entity_name(name: str, kind: str) -> str:
    name = clean_line(name).strip(" :;,.»«\"")
    if kind == "institution":
        name = re.split(
            r"(?=\s+(?:que|dont|lorsque|s'est|a|aux|au|et que)\b)",
            name,
            maxsplit=1,
            flags=re.I,
        )[0]
        name = re.sub(
            r"\s+le\s+\d{1,2}\s+[a-zéûîôàè]+\s+\d{4}$",
            "",
            name,
            flags=re.I,
        )
        name = name.strip(" :;,.»«\"")
    if kind == "organization":
        name = re.sub(r"^(?:L[''])?ASSOCIATION\b", "Association", name, flags=re.I)
    return name


def infer_role(context: str, kind: str = "") -> Optional[str]:
    if kind in ROLE_BLACKLIST_KINDS:
        return None
    short_context = context[:ROLE_WINDOW]
    for pattern, role in ROLE_HINT_PATTERNS:
        if pattern.search(short_context):
            return role
    return None


def infer_side(context: str, kind: str = "") -> Optional[str]:
    if kind in ROLE_BLACKLIST_KINDS:
        return None
    short_context = context[:SIDE_WINDOW]
    for pattern, side in SIDE_HINT_PATTERNS:
        if pattern.search(short_context):
            return side
    return None


def extract_entities(text: str) -> List[Dict[str, Optional[str]]]:
    entities: List[Dict[str, Optional[str]]] = []
    normalized = normalize_space(text)

    for _label, pattern, default_side, kind in PERSON_ENTITY_PATTERNS:
        for match in pattern.finditer(normalized):
            raw_name = match.group(0)
            name = clean_entity_name(raw_name, kind)
            if not name:
                continue
            start = max(0, match.start() - 80)
            end = min(len(normalized), match.end() + 80)
            context = normalized[start:end]
            role = infer_role(context, kind=kind)
            side = infer_side(context, kind=kind) or default_side
            entities.append({
                "name": name,
                "kind": kind,
                "role": role,
                "side": side,
            })

    entities = [e for e in dedupe_entities(entities) if len(e["name"]) <= 120]
    entities.sort(key=lambda x: (x.get("side") is None, x.get("role") is None, x["name"]))
    return entities


# ============================================================
# Parsing
# ============================================================

def parse_document(text: str) -> List[SectionNode]:
    """Parse un document juridique en liste ordonnée de sections logiques."""
    lines = split_lines(text)
    header_registry = extract_header_registry(text)

    heading_idx: List[Tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        hk = heading_level_and_kind(line)
        if hk:
            level, kind = hk
            heading_idx.append((i, level, clean_line(line)))

    if not heading_idx:
        full = normalize_space(text)
        return [
            SectionNode(
                id="S1",
                title="DOCUMENT",
                level=1,
                start_line=0,
                end_line=len(lines) - 1,
                text=full,
                section_type="document",
                path=["DOCUMENT"],
                meta=extract_light_metadata(full, header_registry=header_registry),
            )
        ]

    nodes: List[SectionNode] = []

    first_heading_line = heading_idx[0][0]
    if first_heading_line > 0:
        pre_text = normalize_space("\n".join(lines[:first_heading_line]))
        if pre_text:
            nodes.append(
                SectionNode(
                    id="S0",
                    title="EN-TÊTE",
                    level=1,
                    start_line=0,
                    end_line=first_heading_line - 1,
                    text=pre_text,
                    section_type="header",
                    path=["EN-TÊTE"],
                    meta=extract_light_metadata(pre_text, header_registry=header_registry),
                )
            )

    stack: List[Tuple[int, str]] = []
    inherited_type: Optional[str] = None

    for idx, (line_no, level, title) in enumerate(heading_idx):
        next_line_no = heading_idx[idx + 1][0] if idx + 1 < len(heading_idx) else len(lines)
        body_lines = lines[line_no:next_line_no]
        body_text = normalize_space("\n".join(body_lines))

        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        path = [item[1] for item in stack]

        section_type = guess_section_type(title, inherited=inherited_type)
        if section_type != "argument":
            inherited_type = section_type

        node = SectionNode(
            id=f"S{len(nodes) + 1}",
            title=title,
            level=level,
            start_line=line_no,
            end_line=next_line_no - 1,
            text=body_text,
            section_type=section_type,
            path=path,
            meta=extract_light_metadata(body_text, header_registry=header_registry),
        )
        nodes.append(node)

    return postprocess_nodes(nodes)


def postprocess_nodes(nodes: List[SectionNode]) -> List[SectionNode]:
    if not nodes:
        return nodes

    merged: List[SectionNode] = []
    i = 0
    while i < len(nodes):
        current = nodes[i]
        if (
            i + 1 < len(nodes)
            and current.approx_tokens < 40
            and current.text.strip() == current.title.strip()
        ):
            nxt = nodes[i + 1]
            if nxt.path[: len(current.path)] == current.path:
                nxt.text = normalize_space(current.title + "\n\n" + nxt.text)
                nxt.path = current.path[:-1] + nxt.path[-1:]
                i += 1
                continue
        merged.append(current)
        i += 1

    for idx, node in enumerate(merged, start=1):
        node.id = f"S{idx}"
    return merged


def extract_light_metadata(text: str, header_registry: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    articles = sorted(set(m.group(0) for m in ARTICLE_RE.finditer(text)))
    caselaw = sorted(set(clean_caselaw_match(m.group(0)) for m in CASELAW_RE.finditer(text)))
    amounts = sorted(set(m.group(0) for m in MONEY_RE.finditer(text)))
    dates = sorted(set(m.group(0) for m in DATE_RE.finditer(text)))
    entities = extract_entities(text)

    if header_registry:
        entities = [canonicalize_entity_against_registry(e, header_registry) for e in entities]

    return {
        "approx_tokens": approximate_tokens(text),
        "articles": articles[:30],
        "caselaw": caselaw[:30],
        "amounts": amounts[:30],
        "dates": dates[:30],
        "entities": entities[:20],
    }


# ============================================================
# Packeting algorithm
# ============================================================

def build_packets(
    nodes: List[SectionNode],
    max_input_tokens: int = 42000,
    prompt_budget_tokens: int = 2500,
    output_budget_tokens: int = 3000,
    min_fill_ratio: float = 0.55,
) -> List[Packet]:
    """Regroupe les sections en paquets respectant un budget de tokens."""
    safe_content_budget = max_input_tokens - prompt_budget_tokens - output_budget_tokens
    if safe_content_budget <= 0:
        raise ValueError("Token budget too small after prompt/output reservation.")

    packets: List[Packet] = []
    current: List[SectionNode] = []
    current_tokens = 0

    def flush() -> None:
        nonlocal current, current_tokens
        if not current:
            return
        packets.append(make_packet(len(packets) + 1, current))
        current = []
        current_tokens = 0

    for idx, node in enumerate(nodes):
        node_tokens = node.approx_tokens

        if node_tokens > safe_content_budget:
            flush()
            split_nodes = split_oversized_node(node, safe_content_budget)
            for split_node in split_nodes:
                if split_node.approx_tokens > safe_content_budget:
                    raise ValueError(f"Node {split_node.id} still exceeds safe budget after splitting.")
                packets.append(make_packet(len(packets) + 1, [split_node]))
            continue

        if not current:
            current = [node]
            current_tokens = node_tokens
            continue

        same_parent = shared_parent(current[-1], node)
        would_fit = current_tokens + node_tokens <= safe_content_budget

        if would_fit:
            current.append(node)
            current_tokens += node_tokens
            continue

        fill_ratio = current_tokens / safe_content_budget
        if fill_ratio < min_fill_ratio and same_parent:
            flush()
            current = [node]
            current_tokens = node_tokens
            continue

        flush()
        current = [node]
        current_tokens = node_tokens

    flush()
    return packets


def shared_parent(a: SectionNode, b: SectionNode, depth: int = 2) -> bool:
    return a.path[:depth] == b.path[:depth]


def split_oversized_node(node: SectionNode, safe_content_budget: int, header_registry: Optional[Dict[str, object]] = None) -> List[SectionNode]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", node.text) if p.strip()]
    if len(paragraphs) <= 1:
        paragraphs = split_sentences(node.text)

    groups: List[List[str]] = []
    current_group: List[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = approximate_tokens(para)
        if current_group and current_tokens + para_tokens > safe_content_budget:
            groups.append(current_group)
            current_group = [para]
            current_tokens = para_tokens
        else:
            current_group.append(para)
            current_tokens += para_tokens
    if current_group:
        groups.append(current_group)

    split_nodes: List[SectionNode] = []
    for i, group in enumerate(groups, start=1):
        text = normalize_space("\n\n".join(group))
        split_nodes.append(
            SectionNode(
                id=f"{node.id}_{i}",
                title=f"{node.title} [part {i}/{len(groups)}]",
                level=node.level,
                start_line=node.start_line,
                end_line=node.end_line,
                text=text,
                section_type=node.section_type,
                path=node.path + [f"part {i}/{len(groups)}"],
                meta=extract_light_metadata(text, header_registry=header_registry),
            )
        )
    return split_nodes


def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[\.!?;:])\s+(?=[A-ZÉÈÀÙÂÊÎÔÛÇ])", normalize_space(text))
    return [p.strip() for p in parts if p.strip()]


def make_packet(packet_num: int, nodes: List[SectionNode]) -> Packet:
    titles = [node.title for node in nodes]
    section_types = list(dict.fromkeys(node.section_type for node in nodes))
    total_tokens = sum(node.approx_tokens for node in nodes)

    context_ribbon = {
        "packet_id": f"P{packet_num}",
        "first_path": nodes[0].path,
        "last_path": nodes[-1].path,
        "node_ids": [node.id for node in nodes],
        "titles": titles,
        "section_types": section_types,
        "articles": sorted({a for n in nodes for a in n.meta.get("articles", [])})[:50],
        "caselaw": sorted({c for n in nodes for c in n.meta.get("caselaw", [])})[:50],
        "amounts": sorted({m for n in nodes for m in n.meta.get("amounts", [])})[:50],
        "dates": sorted({d for n in nodes for d in n.meta.get("dates", [])})[:50],
        "entities": dedupe_entities([e for n in nodes for e in n.meta.get("entities", [])])[:25],
    }

    return Packet(
        id=f"P{packet_num}",
        nodes=nodes,
        total_tokens=total_tokens,
        section_types=section_types,
        titles=titles,
        context_ribbon=context_ribbon,
    )


# ============================================================
# Prompt builders
# ============================================================

def build_extraction_system_prompt() -> str:
    """Prompt système pour extraction intermédiaire structurée sur un paquet."""
    return normalize_space(
        """
        Rôle
        Vous êtes un assistant juridique français chargé d'extraire et compresser fidèlement un paquet contigu de conclusions, mémoire ou plaidoirie.

        Objectif
        Produire une représentation intermédiaire structurée, riche et exploitable, sans rédiger le résumé final.
        Cette étape doit préserver au maximum l'information utile du texte source.

        Priorités
        1. Préserver le sens juridique et l'attribution des positions.
        2. Préserver la logique argumentative et l'ordre du texte.
        3. Conserver les dates, montants, articles, jurisprudences, pièces et participants mentionnés.
        4. Être concis sans supprimer les arguments substantiels.

        Règles
        - Utiliser uniquement les informations présentes dans l'entrée.
        - Ne rien inventer.
        - Si une information est incertaine, rester prudent et ne pas extrapoler.
        - Respecter l'ordre des sections et sous-sections du paquet.
        - Conserver les intitulés exacts des titres fournis.
        - Ne pas transformer ce paquet en résumé final littéraire.
        - Ne pas fusionner artificiellement des positions distinctes.
        - Si un passage reproduit la position adverse, l'indiquer explicitement.
        - Le champ "packet_summary" est uniquement un aperçu très bref.
        - Le contenu détaillé doit être conservé dans les sections.
        - Ne pas sur-comprimer les arguments à ce stade.
        - Pour chaque section importante, conserver au moins un extrait source court et fidèle.
        - Pour les sections importantes, conserver également 1 à 3 points verbatim courts lorsque cela aide à préserver la précision juridique ou factuelle.
        - Les extraits source et points verbatim doivent rester courts et strictement issus du texte fourni.
        - Identifier les participants cités dans chaque section avec leur rôle et, si possible, leur camp.
        - Si un bloc contient des prétentions finales, les isoler dans un champ dédié.

        Format de sortie
        Retourner exclusivement un JSON valide conforme au schéma demandé par l'utilisateur.
        """
    )


def build_extraction_user_prompt(packet: Packet) -> str:
    """Construit le prompt utilisateur pour un paquet donné."""
    schema = {
        "packet_id": packet.id,
        "document_role": "appelant|intimé|demandeur|défendeur|inconnu",
        "packet_summary": "Aperçu global très bref du paquet en 5 à 10 lignes maximum.",
        "sections": [
            {
                "title": "Titre exact",
                "path": ["Niveau 1", "Niveau 2"],
                "section_type": "header|facts|procedure|discussion|claims|argument|other",
                "participants": [
                    {
                        "name": "Nom exact",
                        "kind": "person|organization|institution|lawyer|institutional_actor",
                        "role": "président|salarié|appelant|...",
                        "side": "current_party|opposing_party|neutral|null",
                    }
                ],
                "thesis": "Thèse ou fonction principale du bloc.",
                "facts": ["Fait 1", "Fait 2"],
                "arguments": ["Argument 1", "Argument 2"],
                "rebuttals": ["Réfutation 1"],
                "legal_references": ["article ...", "Cass. ..."],
                "pieces_cited": ["Pièce 17"],
                "dates_amounts": ["05 avril 2024", "30 000 €"],
                "requests": ["Demande formulée dans ce bloc"],
                "key_source_excerpt": "Court extrait source fidèle (1 à 3 phrases maximum).",
                "key_verbatim_points": ["Point verbatim court 1", "Point verbatim court 2"],
                "compression_ratio_hint": "low|medium|high",
                "importance": "high|medium|low",
                "argument_density": "high|medium|low"
            }
        ],
        "carry_forward": {
            "main_issues": ["Question 1", "Question 2"],
            "open_threads": ["Point à poursuivre dans le paquet suivant"],
            "claims_block_present": True,
            "participants_to_track": [
                {
                    "name": "Nom exact",
                    "role": "fonction utile pour les paquets suivants",
                    "side": "current_party|opposing_party|neutral|null",
                }
            ],
        }
    }

    return f"""
CONTEXTE DU PAQUET
- Packet id: {packet.id}
- Types de sections: {', '.join(packet.section_types)}
- Titres inclus: {' | '.join(packet.titles)}
- Articles détectés: {', '.join(packet.context_ribbon.get('articles', [])) or 'aucun'}
- Jurisprudences détectées: {', '.join(packet.context_ribbon.get('caselaw', [])) or 'aucune'}
- Dates détectées: {', '.join(packet.context_ribbon.get('dates', [])) or 'aucune'}
- Montants détectés: {', '.join(packet.context_ribbon.get('amounts', [])) or 'aucun'}
- Participants détectés: {json.dumps(packet.context_ribbon.get('entities', []), ensure_ascii=False)}

TÂCHE
Analysez le paquet ci-dessous et retournez un JSON strictement valide.
Le JSON doit suivre cette structure cible :
{json.dumps(schema, ensure_ascii=False, indent=2)}

PAQUET À ANALYSER
{packet.text}
""".strip()


def build_final_system_prompt() -> str:
    """Prompt système pour la synthèse finale à partir des JSON intermédiaires."""
    return normalize_space(
        """
        Rôle
        Vous êtes un assistant juridique français chargé de rédiger un résumé final exploitable à partir de représentations intermédiaires déjà extraites.

        Objectif
        Rédiger un résumé clair, fidèle, structuré et directement utile à un juriste.

        Priorités
        1. Fidélité au contenu extrait.
        2. Respect de la structure juridique utile.
        3. Exhaustivité raisonnable sur les moyens.
        4. Lisibilité professionnelle.

        Règles
        - Utiliser uniquement les données intermédiaires fournies.
        - S'appuyer en priorité sur les champs "key_source_excerpt" et "key_verbatim_points" pour préserver la précision juridique et factuelle.
        - Préserver autant que possible l'attribution des faits, arguments et demandes aux bons participants.
        - Ne pas inventer de faits, d'articles ou de demandes.
        - Préserver l'ordre général du document source.
        - Préserver les intitulés lorsque ceux-ci structurent utilement le raisonnement.
        - Les moyens doivent représenter la partie la plus substantielle du résumé.
        - Si un dispositif final a été identifié, le reproduire aussi fidèlement que possible.
        - Ne pas surcharger le texte d'avertissements méthodologiques.
        """
    )


def build_final_user_prompt(
    extracted_packets_json: List[Dict[str, object]],
    mode: str = "resume_global",
    max_pages_hint: int = 5,
) -> str:
    """Construit le prompt final à partir des JSON intermédiaires."""
    mode_instructions = {
        "resume_global": "Produisez un résumé structuré complet : parties, faits, procédure, prétentions si présentes, puis moyens de façon substantielle. Lorsque les données intermédiaires contiennent des extraits source ou des points verbatim, utilisez-les comme ancrages de fidélité sans transformer le résumé en compilation de citations.",
        "faits_procedure": "Produisez uniquement les faits et la procédure, sans développer les moyens sauf mention minimale de leur objet.",
        "moyens": "Produisez uniquement la synthèse des moyens, en respectant autant que possible la structure argumentative.",
        "rapport": "Produisez un rapport de synthèse professionnel, rédigé, exploitable rapidement par un juriste.",
        "expose_litige": "Produisez un exposé du litige neutre, clair, continu et professionnel à partir des données extraites.",
    }
    selected_instruction = mode_instructions.get(mode, mode_instructions["resume_global"])

    return f"""
MODE DE SORTIE
{mode}

CONSIGNE SPÉCIFIQUE
{selected_instruction}

CONTRAINTE DE LONGUEUR
Visez un document d'environ {max_pages_hint} pages maximum à densité normale.

DONNÉES INTERMÉDIAIRES
{json.dumps(extracted_packets_json, ensure_ascii=False, indent=2)}
""".strip()


# ============================================================
# Main pipeline function
# ============================================================

def parse_and_packetize(
    source_text: str,
    max_input_tokens: int = 42000,
    prompt_budget_tokens: int = 2500,
    output_budget_tokens: int = 3000,
) -> Tuple[List[SectionNode], List[Packet]]:
    """
    Pipeline principal :
    1. parsing du document,
    2. découpage en paquets.
    """
    nodes = parse_document(source_text)
    packets = build_packets(
        nodes,
        max_input_tokens=max_input_tokens,
        prompt_budget_tokens=prompt_budget_tokens,
        output_budget_tokens=output_budget_tokens,
    )
    return nodes, packets


def compute_compressed_tokens(extracted_jsons: List[Dict[str, object]]) -> int:
    """
    Calcule le nombre de tokens du contenu compressé (JSON intermédiaires).
    """
    compressed_text = json.dumps(extracted_jsons, ensure_ascii=False)
    return approximate_tokens(compressed_text)
