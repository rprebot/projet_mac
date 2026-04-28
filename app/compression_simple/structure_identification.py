"""
Identification de structure par patterns regex (approche déterministe).

Remplace l'approche LLM coûteuse et lente par une détection regex rapide et fiable.
Adapté aux conclusions juridiques françaises.
"""

import json
import re
from typing import List, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Comptage de tokens
# ---------------------------------------------------------------------------
try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False


def _heuristic_token_count(text: str) -> int:
    """Estimation rapide : 1 token ≈ 0.75 mot en français juridique."""
    words = len(text.split())
    return round(words * 1.33)


def get_encoder(model: str = "cl100k_base"):
    """
    Retourne un encodeur tiktoken si disponible et accessible,
    None sinon (fallback sur heuristique).
    """
    if not _TIKTOKEN_AVAILABLE:
        return None
    try:
        enc = tiktoken.encoding_for_model(model)
        # Test rapide pour détecter les erreurs réseau au chargement
        enc.encode("test")
        return enc
    except Exception:
        try:
            enc = tiktoken.get_encoding(model)
            enc.encode("test")
            return enc
        except Exception:
            return None


def count_tokens(text: str, encoder) -> int:
    """
    Compte les tokens d'un texte.
    Utilise tiktoken si disponible, sinon l'heuristique mots×1.33.
    """
    if not text:
        return 0
    if encoder is not None:
        return len(encoder.encode(text))
    return _heuristic_token_count(text)


# ---------------------------------------------------------------------------
# Patterns de titres de sections
# ---------------------------------------------------------------------------

# Chaque pattern capture un groupe nommé "title"
HEADING_PATTERNS = [
    # 1. Grandes parties romaines : I. / II. / III. / IV. (tolère espaces en début)
    re.compile(
        r'^\s*(?P<title>(?:I{1,3}V?|VI{0,3}|I[XV]|V?I{0,3})\s*[\.\-–]\s*.{3,120})',
        re.MULTILINE
    ),
    # 2. Sous-parties lettrées : A- / B- / A. / B. (tolère espaces en début)
    re.compile(
        r'^\s*(?P<title>[A-Z]\s*[\-–\.]\s*(?:SUR|S\'AGISSANT|EN DROIT|EN L\'ESP|LE|LES).{3,120})',
        re.MULTILINE
    ),
    # 3. Sous-sous-parties numérotées : 1- EN DROIT / 2- EN L'ESPECE (tolère espaces en début)
    re.compile(
        r'^\s*(?P<title>\d+\s*[-–\.]\s*(?:EN\s|SUR\s|LES\s|LA\s|L\').{3,80})',
        re.MULTILINE
    ),
    # 4. Griefs numérotés (GRIEF 1 à GRIEF 24) (tolère espaces en début)
    re.compile(
        r'^\s*(?P<title>GRIEF\s+\d+\s*:?)',
        re.MULTILINE | re.IGNORECASE
    ),
    # 5. Sections fixes connues du document (tolère espaces en début)
    re.compile(
        r'^\s*(?P<title>'
        r'CONCLUSIONS D\'APPELANT'
        r'|DISCUSSION'
        r'|PAR CES MOTIFS'
        r'|SUR LES DEMANDES INDEMNITAIRES DU SALARIE'
        r'|A TITRE PRELIMINAIRE\s*:.{0,100}'
        r'|À TITRE PRELIMINAIRE\s*:.{0,100}'
        r'|SOUS TOUTES RESERVES'
        r')',
        re.MULTILINE | re.IGNORECASE
    ),
]


# ---------------------------------------------------------------------------
# Détermination du niveau hiérarchique (1 = le plus haut)
# ---------------------------------------------------------------------------

def detect_level(title: str) -> int:
    """Détecte le niveau hiérarchique d'un titre (1 = plus haut, 4 = plus bas)."""
    t = title.strip().upper()

    # Niveau 1 – parties principales romaines ou blocs majeurs
    if re.match(r'^(I{1,3}V?|VI{0,3}|I[XV]|V?I{0,3})\s*[\.\-–]', t):
        return 1
    if t in ("CONCLUSIONS D'APPELANT", "DISCUSSION", "PAR CES MOTIFS", "SOUS TOUTES RESERVES"):
        return 1

    # Niveau 2 – sous-parties lettrées ou préliminaires
    if re.match(r'^[A-Z]\s*[\-–\.]', t):
        return 2
    if t.startswith("A TITRE PRELIMINAIRE") or t.startswith("À TITRE PRELIMINAIRE"):
        return 2
    if t.startswith("SUR LES DEMANDES INDEMNITAIRES"):
        return 2

    # Niveau 3 – sous-sous-parties numérotées
    if re.match(r'^\d+\s*[-–\.]', t):
        return 3

    # Niveau 4 – griefs
    if re.match(r'^GRIEF\s+\d+', t):
        return 4

    return 2  # défaut


# ---------------------------------------------------------------------------
# Extraction des sections (liste plate)
# ---------------------------------------------------------------------------

def is_valid_section_title(title: str, level: int) -> bool:
    """
    Vérifie si un titre est valide (pas juste un fragment de texte).

    Garder les niveaux 1, 2 et 3 (I-, A-, 1-) mais rejeter niveau 4 (GRIEF)
    - Niveau 1 : I., II., III., DISCUSSION, PAR CES MOTIFS, etc.
    - Niveau 2 : A-, B-, préliminaires, etc.
    - Niveau 3 : 1-, 2- (GARDÉ)
    - Niveau 4 : GRIEF (REJETÉ)
    """
    title = title.strip()

    # Rejeter les titres trop courts
    if len(title) < 4:
        return False

    # Rejeter uniquement le niveau 4 (GRIEFS)
    if level >= 4:
        return False

    # Rejeter les titres qui commencent par des caractères invalides
    invalid_starts = ['.', '-', '*', '•', '(', ')', '[', ']', '"', "'"]
    if any(title.startswith(c) for c in invalid_starts):
        return False

    # Rejeter les titres qui sont juste des ponctuations
    if title in ['***', '...', '---', '___']:
        return False

    # Accepter les sections majeures
    valid_keywords = ['SUR', 'DISCUSSION', 'PAR CES MOTIFS', 'CONCLUSIONS',
                      'A TITRE', 'SOUS TOUTES', 'S\'AGISSANT']
    if any(keyword in title.upper() for keyword in valid_keywords):
        return True

    # Accepter les numérotations de tous niveaux (I., A-, 1-, etc.)
    if re.match(r'^(?:I{1,3}V?|VI{0,3}|[A-Z]|\d+)\s*[\.\-–]', title):
        # Mais rejeter si c'est une liste à puces (commence par "- " suivi de minuscule)
        if re.match(r'^[\-–]\s+[a-z]', title):
            return False
        return True

    return False


def extract_sections(text: str, encoder=None) -> List[Dict]:
    """Extrait toutes les sections détectées dans le texte."""
    hits = []
    seen_starts = set()

    for pat in HEADING_PATTERNS:
        for m in pat.finditer(text):
            start = m.start()
            if start in seen_starts:
                continue
            title = m.group("title").strip()

            # Détecter le niveau du titre
            level = detect_level(title)

            # Filtrer les titres invalides (passe le niveau en paramètre)
            if not is_valid_section_title(title, level):
                continue

            seen_starts.add(start)
            hits.append((start, title))

    hits.sort(key=lambda x: x[0])

    sections = []
    for idx, (start, title) in enumerate(hits):
        end = hits[idx + 1][0] if idx + 1 < len(hits) else len(text)
        heading_end = start + len(title)
        body = text[heading_end:end].strip()
        body_preview = " ".join(body.split())[:500] if body else ""
        full_text = (title + "\n" + body).strip()

        sections.append({
            "index": idx + 1,
            "level": detect_level(title),
            "title": title,
            "body": body,
            "body_preview": body_preview,
            "char_start": start,
            "char_end": end,
            "tokens": {
                "title": count_tokens(title, encoder),
                "body": count_tokens(body, encoder),
                "total": count_tokens(full_text, encoder),
            },
        })

    return sections


# ---------------------------------------------------------------------------
# Transformation en arborescence imbriquée
# ---------------------------------------------------------------------------

def nest_sections(flat: List[Dict]) -> List[Dict]:
    """Transforme une liste plate de sections en arborescence imbriquée."""
    root = []
    stack = []  # [(level, node_dict)]

    for sec in flat:
        node = {
            "title": sec["title"],
            "level": sec["level"],
            "body": sec["body"],
            "body_preview": sec["body_preview"],
            "tokens": sec["tokens"],
            "subsections": [],
        }
        while stack and stack[-1][0] >= sec["level"]:
            stack.pop()

        if stack:
            stack[-1][1]["subsections"].append(node)
        else:
            root.append(node)

        stack.append((sec["level"], node))

    return root


# ---------------------------------------------------------------------------
# Classification des sections (Faits, Procédure, Moyens, Prétentions)
# ---------------------------------------------------------------------------

def classify_section_type(title: str, level: int, body: str) -> str:
    """
    Classifie une section selon son type : faits, procedure, moyens, pretentions.
    """
    t = title.strip().upper()

    # Prétentions / Dispositif
    if any(keyword in t for keyword in ["PAR CES MOTIFS", "DISPOSITIF", "IL PLAÎT", "EN CONSÉQUENCE"]):
        return "pretentions"

    # Faits
    if any(keyword in t for keyword in ["FAITS", "RAPPEL DES FAITS", "EXPOSÉ DES FAITS", "CONTEXTE"]):
        return "faits"

    # Procédure
    if any(keyword in t for keyword in ["PROCÉDURE", "PROCEDURE", "RAPPEL DE LA PROCÉDURE"]):
        return "procedure"

    # Moyens / Discussion / Arguments
    if any(keyword in t for keyword in ["DISCUSSION", "MOYENS", "EN DROIT", "GRIEF", "ARGUMENTAIRE"]):
        return "moyens"

    # Par défaut, selon le niveau
    if level == 1:
        return "moyens"  # Les grandes parties sont généralement des moyens

    return "moyens"  # Défaut


def convert_to_simple_compression_format(sections: List[Dict]) -> Dict:
    """
    Convertit la structure détectée en format compatible avec simple_compression.

    Returns:
        {
            "faits": {"sous_sections": [...]},
            "procedure": {"sous_sections": [...]},
            "moyens": {"sous_sections": [...]},
            "pretentions": {"contenu": "...", "tokens": ...}
        }
    """
    structure = {
        "faits": {"sous_sections": []},
        "procedure": {"sous_sections": []},
        "moyens": {"sous_sections": []},
        "pretentions": {"sous_sections": []}
    }

    # Obtenir l'encodeur pour compter les tokens
    encoder = get_encoder()

    for section in sections:
        section_type = classify_section_type(section["title"], section["level"], section["body"])

        if section_type == "faits":
            structure["faits"]["sous_sections"].append({
                "titre": section["title"],
                "contenu": section["body"],
                "tokens": count_tokens(section["body"], encoder),
                "position": section["index"],
                "type": "faits"
            })
        elif section_type == "procedure":
            structure["procedure"]["sous_sections"].append({
                "titre": section["title"],
                "contenu": section["body"],
                "tokens": count_tokens(section["body"], encoder),
                "position": section["index"],
                "type": "procedure"
            })
        elif section_type == "moyens":
            structure["moyens"]["sous_sections"].append({
                "titre": section["title"],
                "contenu": section["body"],
                "tokens": count_tokens(section["body"], encoder),
                "position": section["index"],
                "type": "moyens"
            })
        elif section_type == "pretentions":
            structure["pretentions"]["sous_sections"].append({
                "titre": section["title"],
                "contenu": section["body"],
                "tokens": count_tokens(section["body"], encoder),
                "position": section["index"],
                "type": "pretentions"
            })

    return structure


# ---------------------------------------------------------------------------
# Fonction principale compatible avec simple_compression
# ---------------------------------------------------------------------------

def identify_structure_regex(document: str) -> Dict:
    """
    Identifie la structure d'un document juridique par regex.

    Compatible avec l'interface de simple_compression.

    Args:
        document: Texte complet de la conclusion

    Returns:
        Structure au format simple_compression
    """
    encoder = get_encoder()
    sections = extract_sections(document, encoder=encoder)
    structure = convert_to_simple_compression_format(sections)

    return structure
