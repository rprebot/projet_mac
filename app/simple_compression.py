"""
Module de compression simplifiée pour les conclusions juridiques.

Process en 3 étapes :
1. Identification de la structure (Faits, Procédure, Moyens, Prétentions) via LLM
2. Résumé ciblé des sous-sections de Faits et Procédure (> 7000 tokens → réduction 20%)
3. Reconstitution + application du prompt de résumé final

Auteur: POC_MAC
Date: 2026-04-15
"""

import json
import os
import tiktoken
from typing import Dict, List, Optional, Tuple
from mistralai import Mistral


def estimate_tokens(text: str) -> int:
    """
    Estime le nombre de tokens dans un texte en utilisant tiktoken.

    Args:
        text: Texte à analyser

    Returns:
        Nombre estimé de tokens
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback: approximation 1 token ≈ 4 caractères
        return len(text) // 4


def load_prompt(prompt_name: str) -> str:
    """
    Charge un fichier de prompt depuis le dossier prompts/.

    Args:
        prompt_name: Nom du fichier prompt (sans extension .md)

    Returns:
        Contenu du prompt
    """
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", f"{prompt_name}.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def identify_structure(document: str, api_key: str) -> Dict:
    """
    Identifie la structure du document (sections et sous-sections) via appel LLM.

    Args:
        document: Texte complet de la conclusion
        api_key: Clé API Mistral

    Returns:
        Dictionnaire structuré avec sections et sous-sections
        {
            "faits": {
                "sous_sections": [
                    {"titre": "...", "contenu": "..."},
                    ...
                ]
            },
            "procedure": {...},
            "moyens": {"contenu": "..."},
            "pretentions": {"contenu": "..."}
        }
    """
    client = Mistral(api_key=api_key)

    # Charger le prompt d'identification
    system_prompt = load_prompt("identification_structure")

    # Appel LLM pour extraction de structure
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": document}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    # Parser la réponse JSON
    structure = json.loads(response.choices[0].message.content)
    return structure


def reduce_subsection(subsection_content: str, api_key: str, reduction_pct: float = 20.0) -> str:
    """
    Réduit une sous-section de X% via résumé LLM.

    Args:
        subsection_content: Contenu de la sous-section à réduire
        api_key: Clé API Mistral
        reduction_pct: Pourcentage de réduction cible (défaut: 20%)

    Returns:
        Texte résumé de la sous-section
    """
    client = Mistral(api_key=api_key)

    # Charger le prompt de résumé
    system_prompt = load_prompt("resume_subsection")

    # Calculer la taille cible
    original_tokens = estimate_tokens(subsection_content)
    target_tokens = int(original_tokens * (1 - reduction_pct / 100))

    user_message = f"""Texte à résumer (objectif: réduire de {reduction_pct}% soit environ {target_tokens} tokens) :

{subsection_content}"""

    # Appel LLM pour résumé
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.3,
        max_tokens=target_tokens + 500  # Marge de sécurité
    )

    return response.choices[0].message.content.strip()


def reconstruct_document(structure: Dict) -> str:
    """
    Reconstruit le document complet à partir de la structure (sections réduites + sections intactes).

    Args:
        structure: Dictionnaire avec sections et sous-sections

    Returns:
        Document reconstitué sous forme de texte
    """
    parts = []

    # Section FAITS
    if "faits" in structure and "sous_sections" in structure["faits"]:
        parts.append("# FAITS\n")
        for subsection in structure["faits"]["sous_sections"]:
            titre = subsection.get("titre", "")
            contenu = subsection.get("contenu", "")
            if titre:
                parts.append(f"## {titre}\n")
            parts.append(f"{contenu}\n\n")

    # Section PROCÉDURE
    if "procedure" in structure and "sous_sections" in structure["procedure"]:
        parts.append("# PROCÉDURE\n")
        for subsection in structure["procedure"]["sous_sections"]:
            titre = subsection.get("titre", "")
            contenu = subsection.get("contenu", "")
            if titre:
                parts.append(f"## {titre}\n")
            parts.append(f"{contenu}\n\n")

    # Section MOYENS (intacte)
    if "moyens" in structure and "contenu" in structure["moyens"]:
        parts.append("# MOYENS\n")
        parts.append(f"{structure['moyens']['contenu']}\n\n")

    # Section PRÉTENTIONS (intacte)
    if "pretentions" in structure and "contenu" in structure["pretentions"]:
        parts.append("# PRÉTENTIONS\n")
        parts.append(f"{structure['pretentions']['contenu']}\n\n")

    return "\n".join(parts)


def simple_compression_pipeline(
    document: str,
    api_key: str,
    final_model: str = "mistral-large-latest",
    final_prompt: str = "resume_conclusions",
    threshold_tokens: int = 7000,
    reduction_pct: float = 20.0,
    progress_callback = None
) -> Tuple[str, Dict]:
    """
    Pipeline complet de compression simplifiée.

    Étapes :
    1. Identifier la structure (Faits, Procédure, Moyens, Prétentions)
    2. Réduire les sous-sections de Faits/Procédure > seuil de tokens
    3. Reconstituer le document
    4. Appliquer le prompt de résumé final

    Args:
        document: Texte complet de la conclusion
        api_key: Clé API Mistral
        final_model: Modèle pour le résumé final
        final_prompt: Nom du prompt final (défaut: resume_conclusions)
        threshold_tokens: Seuil pour considérer une sous-section comme "grande" (défaut: 7000)
        reduction_pct: Pourcentage de réduction pour les sous-sections (défaut: 20%)
        progress_callback: Fonction callback pour afficher la progression (Streamlit)

    Returns:
        Tuple (résumé_final, données_intermédiaires)
    """
    intermediary_data = {
        "structure_initiale": None,
        "sous_sections_reduites": [],
        "document_reconstitue": None,
        "tokens_original": estimate_tokens(document),
        "tokens_reconstitue": 0,
        "tokens_final": 0
    }

    # Étape 1 : Identification de la structure
    if progress_callback:
        progress_callback("🔍 Étape 1/4 : Identification de la structure du document...")

    structure = identify_structure(document, api_key)
    intermediary_data["structure_initiale"] = structure

    # Étape 2 : Résumé ciblé des sous-sections volumineuses
    if progress_callback:
        progress_callback("✂️ Étape 2/4 : Résumé des sous-sections volumineuses (Faits/Procédure)...")

    sections_to_reduce = ["faits", "procedure"]

    for section_name in sections_to_reduce:
        if section_name not in structure:
            continue

        if "sous_sections" not in structure[section_name]:
            continue

        for i, subsection in enumerate(structure[section_name]["sous_sections"]):
            contenu = subsection.get("contenu", "")
            tokens = estimate_tokens(contenu)

            if tokens > threshold_tokens:
                if progress_callback:
                    titre = subsection.get("titre", f"Sous-section {i+1}")
                    progress_callback(f"  📝 Réduction de '{titre}' ({tokens} tokens → ~{int(tokens * 0.8)} tokens)...")

                # Réduire la sous-section
                reduced_content = reduce_subsection(contenu, api_key, reduction_pct)
                subsection["contenu"] = reduced_content

                intermediary_data["sous_sections_reduites"].append({
                    "section": section_name,
                    "titre": subsection.get("titre", ""),
                    "tokens_original": tokens,
                    "tokens_reduit": estimate_tokens(reduced_content)
                })

    # Étape 3 : Reconstitution du document
    if progress_callback:
        progress_callback("🔧 Étape 3/4 : Reconstitution du document...")

    reconstructed_doc = reconstruct_document(structure)
    intermediary_data["document_reconstitue"] = reconstructed_doc
    intermediary_data["tokens_reconstitue"] = estimate_tokens(reconstructed_doc)

    # Étape 4 : Application du prompt de résumé final
    if progress_callback:
        progress_callback(f"📋 Étape 4/4 : Application du prompt final '{final_prompt}'...")

    client = Mistral(api_key=api_key)
    final_system_prompt = load_prompt(final_prompt)

    response = client.chat.complete(
        model=final_model,
        messages=[
            {"role": "system", "content": final_system_prompt},
            {"role": "user", "content": reconstructed_doc}
        ],
        temperature=0.3,
        max_tokens=16000
    )

    final_summary = response.choices[0].message.content.strip()
    intermediary_data["tokens_final"] = estimate_tokens(final_summary)

    if progress_callback:
        progress_callback("✅ Pipeline terminé !")

    return final_summary, intermediary_data
