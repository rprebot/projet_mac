"""
Test d'extraction des JSON intermédiaires pour le Dossier 6 - Conclusion intimée.

Ce script exécute les étapes du pipeline de compression standard :
1. Parsing du document en sections
2. Packetisation (découpage en paquets)
3. Extraction JSON intermédiaire pour chaque paquet via Mistral API

Les résultats sont sauvegardés dans le dossier TEST_COMPRESSION/output/
"""

import json
import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ajouter le dossier app au path pour les imports
APP_DIR = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

from dotenv import load_dotenv
from mistralai import Mistral

from document_compression import (
    parse_and_packetize,
    build_extraction_system_prompt,
    build_extraction_user_prompt,
    compute_compressed_tokens,
    approximate_tokens,
)

# Charger les variables d'environnement
load_dotenv(Path(__file__).parent.parent / ".env")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Fichier source
DOSSIER_PATH = APP_DIR / "dossiers" / "Dossier_6_conclusion_appelant.txt"
OUTPUT_DIR = Path(__file__).parent / "output"

MODEL = "mistral-large-latest"


def call_extraction(system_prompt: str, messages: list, max_retries: int = 2) -> str:
    """Appelle l'API Mistral pour l'extraction JSON d'un paquet, avec retry."""
    client = Mistral(api_key=MISTRAL_API_KEY, timeout_ms=300_000)
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.complete(
                model=MODEL,
                messages=full_messages,
                temperature=0.0,
                max_tokens=32000,
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < max_retries:
                wait = 10 * (attempt + 1)
                print(f"      ⚠️  Tentative {attempt+1} échouée ({e}), retry dans {wait}s...", flush=True)
                time.sleep(wait)
            else:
                raise


def main():
    if not MISTRAL_API_KEY:
        print("ERREUR: MISTRAL_API_KEY non configurée dans .env")
        sys.exit(1)

    # Lire le document
    print(f"📄 Lecture du document: {DOSSIER_PATH.name}")
    document = DOSSIER_PATH.read_text(encoding="utf-8")
    tokens_original = approximate_tokens(document)
    print(f"   {len(document):,} caractères, ~{tokens_original:,} tokens\n")

    # ÉTAPE 1 & 2 : Parsing + Packetisation
    print("=" * 60)
    print("ÉTAPE 1/2 - Parsing & Packetisation")
    print("=" * 60)

    nodes, packets = parse_and_packetize(
        document,
        max_input_tokens=20000,
        prompt_budget_tokens=2500,
        output_budget_tokens=3000,
    )

    print(f"   Sections détectées : {len(nodes)}")
    print(f"   Paquets créés      : {len(packets)}")
    for i, pkt in enumerate(packets):
        print(f"   - Paquet {i+1}: {pkt.total_tokens:,} tokens, {len(pkt.nodes)} sections")
        for title in pkt.titles[:5]:
            print(f"     └─ {title}")
    print()

    # Sauvegarder la structure des paquets
    OUTPUT_DIR.mkdir(exist_ok=True)
    packets_info = []
    for i, pkt in enumerate(packets):
        packets_info.append({
            "packet_id": pkt.id,
            "total_tokens": pkt.total_tokens,
            "nb_sections": len(pkt.nodes),
            "titles": pkt.titles,
            "section_types": pkt.section_types,
        })
    with open(OUTPUT_DIR / "01_packets_structure.json", "w", encoding="utf-8") as f:
        json.dump(packets_info, f, ensure_ascii=False, indent=2)
    print(f"   Structure sauvegardée: output/01_packets_structure.json\n")

    # ÉTAPE 3 : Extraction JSON pour chaque paquet
    print("=" * 60)
    print(f"ÉTAPE 2/2 - Extraction JSON ({len(packets)} paquets) via {MODEL}")
    print("=" * 60)

    extraction_system_prompt = build_extraction_system_prompt()
    extracted_jsons = {}
    start_time = time.time()

    def extract_one(packet, index):
        t0 = time.time()
        print(f"   🔄 Paquet {index+1}/{len(packets)} - envoi...", flush=True)
        user_prompt = build_extraction_user_prompt(packet)
        messages = [{"role": "user", "content": user_prompt}]
        response = call_extraction(extraction_system_prompt, messages)

        elapsed = time.time() - t0
        print(f"   📥 Paquet {index+1} - réponse reçue en {elapsed:.1f}s ({len(response)} chars)", flush=True)

        # Sauvegarder la réponse brute dans tous les cas
        raw_file = f"02_extraction_paquet_{index+1}_RAW.txt"
        with open(OUTPUT_DIR / raw_file, "w", encoding="utf-8") as f:
            f.write(response)

        # Nettoyer la réponse (enlever les blocs markdown ```json ... ```)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            # Retirer la première ligne (```json) et la dernière (```)
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:])
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3].rstrip()

        # Parser le JSON (avec tentative de réparation si tronqué)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Tenter de réparer un JSON tronqué en fermant les structures ouvertes
            repaired = cleaned.rstrip().rstrip(",")
            open_braces = repaired.count("{") - repaired.count("}")
            open_brackets = repaired.count("[") - repaired.count("]")
            repaired += "]" * max(0, open_brackets) + "}" * max(0, open_braces)
            parsed = json.loads(repaired)
            print(f"   ⚠️  Paquet {index+1} - JSON tronqué, réparé (fermé {open_brackets} crochets, {open_braces} accolades)", flush=True)
        print(f"   ✅ Paquet {index+1} - JSON parsé OK", flush=True)
        return index, parsed, response

    # Extraction séquentielle (1 worker pour éviter les timeouts)
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {
            executor.submit(extract_one, pkt, i): i
            for i, pkt in enumerate(packets)
        }
        for future in as_completed(futures):
            try:
                idx, parsed_json, raw_response = future.result()
                extracted_jsons[idx] = parsed_json

                # Sauvegarder chaque JSON intermédiaire individuellement
                filename = f"02_extraction_paquet_{idx+1}.json"
                with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
                    json.dump(parsed_json, f, ensure_ascii=False, indent=2)

            except Exception as e:
                print(f"   ❌ Paquet {futures[future]+1} - Erreur: {e}")

    total_elapsed = time.time() - start_time
    print(f"\n   Temps total extraction: {total_elapsed:.1f}s")

    # Reconstituer dans l'ordre
    ordered_jsons = [extracted_jsons[i] for i in range(len(packets)) if i in extracted_jsons]

    # Sauvegarder tous les JSON combinés
    with open(OUTPUT_DIR / "03_all_extractions.json", "w", encoding="utf-8") as f:
        json.dump(ordered_jsons, f, ensure_ascii=False, indent=2)

    # Stats finales
    tokens_compressed = compute_compressed_tokens(ordered_jsons)
    ratio = round((1 - tokens_compressed / tokens_original) * 100, 1) if tokens_original > 0 else 0

    print(f"\n{'=' * 60}")
    print(f"RÉSULTATS")
    print(f"{'=' * 60}")
    print(f"   Tokens original   : {tokens_original:,}")
    print(f"   Tokens compressé  : {tokens_compressed:,}")
    print(f"   Ratio compression : {ratio}%")
    print(f"   Paquets extraits  : {len(ordered_jsons)}/{len(packets)}")
    print(f"\n   Fichiers sauvegardés dans: {OUTPUT_DIR}/")
    print(f"   - 01_packets_structure.json     (structure des paquets)")
    for i in range(len(ordered_jsons)):
        print(f"   - 02_extraction_paquet_{i+1}.json  (JSON intermédiaire)")
    print(f"   - 03_all_extractions.json       (tous les JSON combinés)")


if __name__ == "__main__":
    main()
