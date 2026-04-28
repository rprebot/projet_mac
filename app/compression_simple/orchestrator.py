"""
Orchestrateur du pipeline de compression simplifiée.

Ce module coordonne les 4 étapes du pipeline :
1. Identification de la structure
2. Réduction des sous-sections volumineuses
3. Reconstitution du document
4. Génération du résumé final
"""
from typing import Tuple, Dict, Optional, Callable
from mistralai import Mistral

from .structure_identification import identify_structure_regex
from .subsection_reduction import reduce_subsection
from .document_reconstruction import reconstruct_document
from .utils import estimate_tokens, load_prompt


def run_simple_compression_pipeline(
    document: str,
    api_key: str,
    final_model: str = "mistral-large-latest",
    final_prompt: str = "resume_conclusions",
    threshold_tokens: int = 7000,
    reduction_pct: float = 20.0,
    progress_callback: Optional[Callable[[str], None]] = None
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
        final_model: Modèle pour le résumé final (défaut: mistral-large-latest)
        final_prompt: Nom du prompt final (défaut: resume_conclusions)
        threshold_tokens: Seuil pour considérer une sous-section comme "grande" (défaut: 7000)
        reduction_pct: Pourcentage de réduction pour les sous-sections (défaut: 20%)
        progress_callback: Fonction callback pour afficher la progression (Streamlit)

    Returns:
        Tuple (résumé_final, données_intermédiaires)

        données_intermédiaires = {
            "structure_initiale": dict,
            "sous_sections_reduites": list,
            "document_reconstitue": str,
            "tokens_original": int,
            "tokens_reconstitue": int,
            "tokens_final": int
        }
    """
    intermediary_data = {
        "structure_initiale": None,
        "sous_sections_reduites": [],
        "document_reconstitue": None,
        "tokens_original": estimate_tokens(document),
        "tokens_reconstitue": 0,
        "tokens_final": 0
    }

    # ========================================================================
    # ÉTAPE 1 : Identification de la structure (REGEX - instantané)
    # ========================================================================
    if progress_callback:
        progress_callback("🔍 Étape 1/4 : Identification de la structure du document (regex)...")

    structure = identify_structure_regex(document)
    intermediary_data["structure_initiale"] = structure

    # ========================================================================
    # ÉTAPE 2 : Résumé ciblé des sous-sections volumineuses
    # ========================================================================
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

    # ========================================================================
    # ÉTAPE 3 : Reconstitution du document
    # ========================================================================
    if progress_callback:
        progress_callback("🔧 Étape 3/4 : Reconstitution du document...")

    reconstructed_doc = reconstruct_document(structure)
    intermediary_data["document_reconstitue"] = reconstructed_doc
    intermediary_data["tokens_reconstitue"] = estimate_tokens(reconstructed_doc)

    # ========================================================================
    # ÉTAPE 4 : Application du prompt de résumé final
    # ========================================================================
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
