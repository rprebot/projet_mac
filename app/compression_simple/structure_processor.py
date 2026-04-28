"""
Module unifié : identification de structure + réduction de sections volumineuses.

Ce module combine l'identification regex de structure et la réduction de sections
pour produire une structure finale optimisée pour la compression.
"""

import json
import re
import time
from typing import List, Dict, Optional, Tuple
from mistralai import Mistral

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

HEADING_PATTERNS = [
    # 1. Grandes parties romaines : I. / II. / III. / IV.
    re.compile(
        r'^\s*(?P<title>(?:I{1,3}V?|VI{0,3}|I[XV]|V?I{0,3})\s*[\.\-–]\s*.{3,120})',
        re.MULTILINE
    ),
    # 2. Sous-parties lettrées : A- / B- / A. / B.
    re.compile(
        r'^\s*(?P<title>[A-Z]\s*[\-–\.]\s*(?:SUR|S\'AGISSANT|EN DROIT|EN L\'ESP|LE|LES).{3,120})',
        re.MULTILINE
    ),
    # 3. Sous-sous-parties numérotées : 1- EN DROIT / 2- EN L'ESPECE
    re.compile(
        r'^\s*(?P<title>\d+\s*[-–\.]\s*(?:EN\s|SUR\s|LES\s|LA\s|L\').{3,80})',
        re.MULTILINE
    ),
    # 4. Griefs numérotés (GRIEF 1 à GRIEF 24)
    re.compile(
        r'^\s*(?P<title>GRIEF\s+\d+\s*:?)',
        re.MULTILINE | re.IGNORECASE
    ),
    # 5. Sections fixes connues du document
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
# Détermination du niveau hiérarchique
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


def is_valid_section_title(title: str, level: int) -> bool:
    """
    Vérifie si un titre est valide (pas juste un fragment de texte).

    Garder les niveaux 1, 2 et 3 (I-, A-, 1-) mais rejeter niveau 4 (GRIEF)
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


# ---------------------------------------------------------------------------
# Extraction des sections (liste plate)
# ---------------------------------------------------------------------------

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

            # Filtrer les titres invalides
            if not is_valid_section_title(title, level):
                continue

            seen_starts.add(start)
            hits.append((start, title, level))

    hits.sort(key=lambda x: x[0])

    sections = []
    for idx, (start, title, level) in enumerate(hits):
        end = hits[idx + 1][0] if idx + 1 < len(hits) else len(text)
        heading_end = start + len(title)
        body = text[heading_end:end].strip()
        body_preview = " ".join(body.split())[:500] if body else ""
        full_text = (title + "\n" + body).strip()

        sections.append({
            "index": idx + 1,
            "level": level,
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
# Réduction des sections volumineuses
# ---------------------------------------------------------------------------

def load_reduction_prompt() -> str:
    """Retourne le prompt système pour la réduction de sections."""
    return """Tu es un assistant juridique spécialisé dans la synthèse de conclusions d'avocats.

Ta tâche est de résumer une section ou sous-section en conservant :
- Tous les arguments juridiques essentiels
- Les références légales et jurisprudentielles importantes
- La structure logique de l'argumentation
- Le vocabulaire juridique précis

Produis un résumé concis qui capture l'essence des arguments sans perdre les points cruciaux."""


def reduce_section(section_content: str, api_key: str, reduction_pct: float = 20.0) -> str:
    """
    Réduit une section volumineuse via résumé LLM.

    Si la section > 15k tokens, la divise en chunks et réduit chaque chunk séparément.

    Args:
        section_content: Contenu de la section à réduire
        api_key: Clé API Mistral
        reduction_pct: Pourcentage de réduction cible (défaut: 20%)

    Returns:
        Texte résumé de la section
    """
    client = Mistral(api_key=api_key)
    encoder = get_encoder()

    # Calculer la taille originale
    original_tokens = count_tokens(section_content, encoder)

    # Si la section est très volumineuse (> 8k tokens), diviser en chunks
    CHUNK_SIZE = 8000  # tokens par chunk
    if original_tokens > CHUNK_SIZE:
        print(f"      ⚠️  Section très volumineuse ({original_tokens:,} tokens), division en chunks...")

        # Diviser le texte en paragraphes
        paragraphs = section_content.split('\n\n')

        chunks = []
        current_chunk = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = count_tokens(para, encoder)
            if current_tokens + para_tokens > CHUNK_SIZE and current_chunk:
                # Chunk complet, le sauvegarder
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_tokens = para_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens

        # Ajouter le dernier chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        print(f"      → Divisé en {len(chunks)} chunks")

        # Réduire chaque chunk
        reduced_chunks = []
        for i, chunk in enumerate(chunks, 1):
            chunk_tokens = count_tokens(chunk, encoder)
            target_tokens = int(chunk_tokens * (1 - reduction_pct / 100))

            print(f"      → Chunk {i}/{len(chunks)} : {chunk_tokens:,} tokens...", end=" ", flush=True)

            user_message = f"""Texte à résumer (objectif: réduire de {reduction_pct}% soit environ {target_tokens} tokens) :

{chunk}"""

            # Retry avec backoff exponentiel
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.chat.complete(
                        model="mistral-large-latest",
                        messages=[
                            {"role": "system", "content": load_reduction_prompt()},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=0.3,
                    )

                    reduced_chunk = response.choices[0].message.content.strip()
                    reduced_chunks.append(reduced_chunk)

                    new_tokens = count_tokens(reduced_chunk, encoder)
                    print(f"→ {new_tokens:,} tokens")
                    break  # Succès, sortir de la boucle retry

                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 1s, 2s, 4s
                        print(f"erreur, retry dans {wait_time}s...", end=" ", flush=True)
                        time.sleep(wait_time)
                    else:
                        print(f"ÉCHEC après {max_retries} tentatives")
                        raise

            # Petit délai entre les chunks
            if i < len(chunks):
                time.sleep(1)

        # Recombiner les chunks
        return '\n\n'.join(reduced_chunks)

    else:
        # Section de taille raisonnable, réduction directe
        target_tokens = int(original_tokens * (1 - reduction_pct / 100))

        user_message = f"""Texte à résumer (objectif: réduire de {reduction_pct}% soit environ {target_tokens} tokens) :

{section_content}"""

        # Appel LLM pour résumé
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": load_reduction_prompt()},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()


def apply_reduction_to_structure(
    sections: List[Dict],
    api_key: str,
    threshold_tokens: int = 7000,
    reduction_pct: float = 20.0
) -> List[Dict]:
    """
    Applique la réduction aux sections qui dépassent le seuil de tokens.

    Args:
        sections: Liste de sections (plate)
        api_key: Clé API Mistral
        threshold_tokens: Seuil en tokens au-delà duquel on réduit (défaut: 7000)
        reduction_pct: Pourcentage de réduction cible (défaut: 20%)

    Returns:
        Liste de sections avec body réduit si nécessaire
    """
    encoder = get_encoder()
    reduced_sections = []

    for section in sections:
        section_copy = section.copy()
        body_tokens = section["tokens"]["body"]

        if body_tokens > threshold_tokens:
            print(f"🔄 Réduction de '{section['title'][:60]}...' ({body_tokens} tokens)")

            # Réduire le body
            reduced_body = reduce_section(section["body"], api_key, reduction_pct)
            section_copy["body"] = reduced_body
            section_copy["body_preview"] = " ".join(reduced_body.split())[:500]

            # Recalculer les tokens
            full_text = (section["title"] + "\n" + reduced_body).strip()
            section_copy["tokens"] = {
                "title": count_tokens(section["title"], encoder),
                "body": count_tokens(reduced_body, encoder),
                "total": count_tokens(full_text, encoder),
            }

            new_tokens = section_copy["tokens"]["body"]
            print(f"   ✅ {body_tokens} → {new_tokens} tokens (-{100*(1-new_tokens/body_tokens):.1f}%)")

        reduced_sections.append(section_copy)

    return reduced_sections


# ---------------------------------------------------------------------------
# Classification des sections
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


def convert_to_compression_format(sections: List[Dict]) -> Dict:
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
# Fonction principale : pipeline complet
# ---------------------------------------------------------------------------

def process_structure(
    document: str,
    api_key: Optional[str] = None,
    apply_reduction: bool = False,
    threshold_tokens: int = 7000,
    reduction_pct: float = 20.0
) -> Dict:
    """
    Pipeline complet : identification + réduction optionnelle.

    Args:
        document: Texte complet du document
        api_key: Clé API Mistral (requise si apply_reduction=True)
        apply_reduction: Si True, réduit les sections > threshold_tokens
        threshold_tokens: Seuil en tokens pour la réduction (défaut: 7000)
        reduction_pct: Pourcentage de réduction cible (défaut: 20%)

    Returns:
        Structure au format simple_compression avec sections éventuellement réduites
    """
    encoder = get_encoder()

    # Étape 1 : Extraction des sections
    print("📝 Extraction des sections...")
    sections = extract_sections(document, encoder=encoder)
    print(f"   ✅ {len(sections)} sections détectées")

    # Étape 2 : Réduction optionnelle
    if apply_reduction:
        if not api_key:
            raise ValueError("api_key requis pour la réduction de sections")
        print(f"\n🔄 Application de la réduction (seuil: {threshold_tokens} tokens, cible: -{reduction_pct}%)...")
        sections = apply_reduction_to_structure(sections, api_key, threshold_tokens, reduction_pct)

    # Étape 3 : Conversion au format final
    print("\n📦 Conversion au format de compression...")
    structure = convert_to_compression_format(sections)

    print("✅ Structure traitée avec succès!")
    return structure
