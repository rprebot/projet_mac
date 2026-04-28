"""
Constantes et patterns regex pour le parsing de documents juridiques.
"""
import re
from typing import List, Tuple, Optional

# Patterns de détection de types de sections
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

# Patterns de détection de titres/headings
HEADING_PATTERNS: List[Tuple[int, re.Pattern[str], str]] = [
    (1, re.compile(r"^\s*[IVXLCDM]+\s*[\.-]\s+.+$"), "roman"),
    (1, re.compile(r"^\s*[IVXLCDM]+\s*$"), "roman_only"),
    (2, re.compile(r"^\s*[A-Z]\s*-\s+.+$"), "alpha"),
    (3, re.compile(r"^\s*\d+\s*[-°\.)]\s+.+$"), "numeric"),
    (3, re.compile(r"^\s*GRIEF\s*\d+\s*:?\s*$", re.I), "grief"),
    (4, re.compile(r"^\s*[a-z]\)\s+.+$"), "subalpha"),
    (1, re.compile(r"^\s*[A-ZÉÈÀÙÂÊÎÔÛÇ'\-\s]{6,}\s*$"), "caps"),
]

# Patterns pour extraction de métadonnées
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

# Patterns pour extraction d'entités (personnes, organisations, etc.)
PERSON_ENTITY_PATTERNS: List[Tuple[str, re.Pattern[str], Optional[str], Optional[str]]] = [
    ("lawyer", re.compile(r"\bMa[iî]tre\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", re.I), "neutral", "lawyer"),
    ("person", re.compile(r"\b(?:Monsieur|Madame|M\.)\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", re.I), None, "person"),
    ("association", re.compile(r"\b(?:L[''])?ASSOCIATION\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", re.I), None, "organization"),
    ("societe", re.compile(r"\b(?:Soci[ée]t[ée]|SARL|SAS|SA|SCI)\s+\[[^\]]+\](?:\s+\[[^\]]+\])*", re.I), None, "organization"),
    ("jurisdiction", re.compile(r"\b(?:Conseil de prud['']hommes|Cour d['']appel|Cour de cassation|Tribunal judiciaire)\b", re.I), "neutral", "institution"),
    ("occupational_physician", re.compile(r"\bm[ée]decin du travail\b", re.I), "neutral", "institutional_actor"),
]

# Patterns pour inférence de rôles
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

# Patterns pour inférence de camp (partie courante vs adverse)
SIDE_HINT_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bappelant[e]?\b", re.I), "current_party"),
    (re.compile(r"\bintim[ée]?\b", re.I), "opposing_party"),
    (re.compile(r"\bdemandeur\b", re.I), "current_party"),
    (re.compile(r"\bd[ée]fendeur\b", re.I), "opposing_party"),
    (re.compile(r"\bemployeur\b", re.I), "current_party"),
    (re.compile(r"\bsalari[ée]\b", re.I), "opposing_party"),
]

# Configuration pour inférence de rôles/camps
ROLE_BLACKLIST_KINDS = {"institution", "institutional_actor"}
ROLE_WINDOW = 80
SIDE_WINDOW = 80
