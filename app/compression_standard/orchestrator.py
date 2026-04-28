"""
Orchestrateur du pipeline de compression standard (par paquets).

Ce module coordonne les étapes du pipeline:
1. Parsing du document en sections
2. Packetisation (découpage en paquets)
3. Extraction JSON pour chaque paquet
4. Génération du résumé final
"""
from typing import Dict, Callable, Optional

# Import du code existant dans document_compression.py
# TODO: Refactoriser pour utiliser des modules séparés
import sys
from pathlib import Path

# Ajouter le dossier parent pour importer document_compression
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from document_compression import (
    parse_and_packetize,
    build_extraction_system_prompt,
    build_extraction_user_prompt,
    build_final_system_prompt,
    build_final_user_prompt,
    compute_compressed_tokens,
    approximate_tokens as approx_tokens_simple,
)


def run_standard_compression_pipeline(
    document: str,
    model_choice: str,
    prompt_type: str = "resume_conclusions",
    progress_callback: Optional[Callable[[str], None]] = None,
    call_model_fn: Optional[Callable] = None,
    call_extraction_fn: Optional[Callable] = None,
) -> Dict:
    """
    Pipeline complet de compression standard (par paquets).

    Étapes :
    1. Parser le document en sections
    2. Découper en paquets
    3. Extraire un JSON intermédiaire pour chaque paquet (en parallèle)
    4. Générer le résumé final à partir des JSON intermédiaires

    Args:
        document: Texte complet du document
        model_choice: Modèle LLM à utiliser pour la synthèse finale
        prompt_type: Type de prompt ("resume_conclusions" ou "rapport_synthese")
        progress_callback: Fonction callback pour afficher la progression
        call_model_fn: Fonction pour appeler le modèle (synthèse finale)
        call_extraction_fn: Fonction pour appeler le modèle (extraction paquets)

    Returns:
        dict avec les clés:
        - "nb_sections": nombre de sections détectées
        - "nb_packets": nombre de paquets créés
        - "extracted_jsons": liste des JSON intermédiaires
        - "final_system_prompt": prompt système utilisé pour la synthèse
        - "final_user_prompt": prompt user utilisé pour la synthèse
        - "final_response": le résumé final
        - "tokens_original": nombre de tokens du document original
        - "tokens_compressed": nombre de tokens après compression
        - "compression_ratio": ratio de compression en %
    """
    import time
    import sys
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    start_time = time.time()

    def log(msg):
        """Log avec timestamp et flush immédiat"""
        elapsed = time.time() - start_time
        print(f"[{elapsed:6.1f}s] {msg}", flush=True)

    print("\n" + "="*60, flush=True)
    log("🚀 PIPELINE DE COMPRESSION STANDARD - DÉBUT")
    print("="*60, flush=True)
    log(f"📋 Modèle sélectionné: {model_choice}")

    # Calculer les tokens du document original
    tokens_original = approx_tokens_simple(document)
    log(f"📄 Document original: {len(document):,} caractères, ~{tokens_original:,} tokens")

    # ========================================================================
    # ÉTAPE 1 & 2 : Parsing et Packetisation
    # ========================================================================
    log("📊 ÉTAPE 1/3 - Parsing & Packetisation...")
    if progress_callback:
        progress_callback(f"Analyse du document ({tokens_original:,} tokens)...")

    nodes, packets = parse_and_packetize(
        document,
        max_input_tokens=20000,
        prompt_budget_tokens=2500,
        output_budget_tokens=3000,
    )

    nb_sections = len(nodes)
    nb_packets = len(packets)

    log(f"   ✅ Parsing terminé: {nb_sections} sections détectées")
    log(f"   ✅ Packetisation: {nb_packets} paquets créés")

    if progress_callback:
        progress_callback(f"Document découpé : {nb_sections} sections, {nb_packets} paquet(s)")

    # ========================================================================
    # ÉTAPE 3 : Extraction JSON pour chaque paquet (EN PARALLÈLE)
    # ========================================================================
    log(f"📊 ÉTAPE 2/3 - Extraction LLM ({nb_packets} paquets) - MODE PARALLÈLE")
    extraction_system_prompt = build_extraction_system_prompt()

    extracted_jsons_dict = {}
    max_workers = 1  # Séquentiel pour éviter les timeouts API

    progress_lock = threading.Lock()

    def clean_and_parse_json(response_text):
        """Nettoie la réponse LLM (blocs markdown, etc.) et parse le JSON."""
        import json
        import re

        # Nettoyer les blocs markdown ```json ... ```
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:])
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3].rstrip()

        # Tentative 1 : tel quel
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Tentative 2 : extraire entre premier { et dernier }
        json_start = cleaned.find('{')
        json_end = cleaned.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = cleaned[json_start:json_end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
            # Tentative 3 : nettoyer les virgules trailing
            json_str_clean = re.sub(r',\s*([}\]])', r'\1', json_str)
            return json.loads(json_str_clean)

        raise ValueError("Aucun JSON valide trouvé dans la réponse")

    # Fonction d'extraction pour un paquet (compatible avec l'app.py existant)
    def extract_packet_parallel(packet, packet_index):
        """Extrait un paquet en utilisant call_extraction_fn"""
        log(f"      └─ 🔄 PAQUET {packet_index+1} - Début extraction...")

        extraction_user_prompt = build_extraction_user_prompt(packet)
        messages = [{"role": "user", "content": extraction_user_prompt}]

        try:
            response = call_extraction_fn(extraction_system_prompt, messages)
            log(f"         └─ 📥 Réponse reçue: {len(response)} chars")

            extracted_json = clean_and_parse_json(response)

            log(f"         └─ ✅ JSON parsé pour paquet {packet_index+1}")
            return (packet_index, packet, extracted_json, None)

        except Exception as e:
            error_msg = f"Erreur extraction paquet {packet_index+1}: {str(e)}"
            log(f"         └─ ❌ {error_msg[:120]}")
            error_result = {
                "packet_id": packet.id,
                "error": error_msg
            }
            return (packet_index, packet, error_result, error_msg)

    # Extraction parallèle
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_packet = {
            executor.submit(extract_packet_parallel, packet, i): (i, packet)
            for i, packet in enumerate(packets)
        }

        completed_count = 0
        for future in as_completed(future_to_packet):
            packet_index, packet, extracted_json, error = future.result()
            completed_count += 1

            with progress_lock:
                if progress_callback:
                    progress_callback(f"Extraction : {completed_count}/{nb_packets} paquets traités")

            extracted_jsons_dict[packet_index] = extracted_json

    # Reconstituer dans l'ordre
    extracted_jsons = [extracted_jsons_dict[i] for i in range(nb_packets)]
    log(f"   ✅ Extraction parallèle terminée: {len(extracted_jsons)} paquets traités")

    # Calculer les tokens compressés
    tokens_compressed = compute_compressed_tokens(extracted_jsons)
    compression_ratio = round((1 - tokens_compressed / tokens_original) * 100, 1) if tokens_original > 0 else 0

    log(f"📊 RÉSULTAT COMPRESSION INTERMÉDIAIRE")
    log(f"   └─ Tokens original: {tokens_original:,}")
    log(f"   └─ Tokens compressé: {tokens_compressed:,}")
    log(f"   └─ Ratio de compression: {compression_ratio}%")

    if progress_callback:
        progress_callback(f"Compression : {tokens_original:,} → {tokens_compressed:,} tokens ({compression_ratio}% de réduction)")

    # ========================================================================
    # ÉTAPE 4 : Génération du résumé final
    # ========================================================================
    log(f"📊 ÉTAPE 3/3 - Génération du résumé final")
    if progress_callback:
        progress_callback("Génération du résumé final...")

    final_system_prompt = build_final_system_prompt(prompt_type)
    final_user_prompt = build_final_user_prompt(
        extracted_jsons,
        mode="resume_global",
        max_pages_hint=5
    )

    log(f"   └─ 📡 Envoi requête API finale ({model_choice})...")
    messages = [{"role": "user", "content": final_user_prompt}]
    final_response = call_model_fn(model_choice, final_system_prompt, messages)

    final_response_tokens = approx_tokens_simple(final_response)
    log(f"   └─ 📥 Réponse finale reçue: ~{final_response_tokens:,} tokens")

    print("\n" + "="*60, flush=True)
    log(f"✅ PIPELINE TERMINÉ")
    log(f"   📄 {tokens_original:,} tokens → 📦 {tokens_compressed:,} tokens → 📝 {final_response_tokens:,} tokens")
    print("="*60 + "\n", flush=True)

    return {
        "nb_sections": nb_sections,
        "nb_packets": nb_packets,
        "extracted_jsons": extracted_jsons,
        "final_system_prompt": final_system_prompt,
        "final_user_prompt": final_user_prompt,
        "final_response": final_response,
        "tokens_original": tokens_original,
        "tokens_compressed": tokens_compressed,
        "compression_ratio": compression_ratio
    }
