"""
Pipeline complet de compression pour le dossier 6.
Réduit de 20% toutes les sections > 10000 tokens et reconstruit le document.
"""
import json
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, 'app')

from compression_simple.structure_identification import identify_structure_regex
from compression_simple.subsection_reduction import reduce_subsection
from compression_simple.document_reconstruction import reconstruct_document
from compression_simple.utils import estimate_tokens

# Charger les variables d'environnement
load_dotenv('.env')
api_key = os.getenv('MISTRAL_API_KEY')

if not api_key:
    print("❌ Erreur: MISTRAL_API_KEY non trouvée dans .env")
    sys.exit(1)

print("="*80)
print("🚀 PIPELINE DE COMPRESSION SIMPLIFIÉE - DOSSIER 6")
print("="*80)

# Configuration
THRESHOLD_TOKENS = 10000
REDUCTION_PCT = 20.0

print(f"\n⚙️  Configuration:")
print(f"   • Seuil de réduction: {THRESHOLD_TOKENS:,} tokens")
print(f"   • Taux de réduction: {REDUCTION_PCT}%")
print()

# ========================================================================
# ÉTAPE 1 : Chargement du document
# ========================================================================
print("📄 Étape 1/4 : Chargement du document...")

with open("app/dossiers/Dossier_6_conclusion_appelant.txt", "r", encoding="utf-8") as f:
    document = f.read()

tokens_original = estimate_tokens(document)
print(f"   ✅ Document chargé: {len(document):,} caractères, ~{tokens_original:,} tokens")

# ========================================================================
# ÉTAPE 2 : Identification de la structure (REGEX)
# ========================================================================
print("\n🔍 Étape 2/4 : Identification de la structure (regex)...")

structure = identify_structure_regex(document)

# Compter les sections
nb_faits = len(structure.get('faits', {}).get('sous_sections', []))
nb_procedure = len(structure.get('procedure', {}).get('sous_sections', []))
nb_moyens = len(structure.get('moyens', {}).get('sous_sections', []))
nb_pretentions = len(structure.get('pretentions', {}).get('sous_sections', []))

print(f"   ✅ Structure identifiée:")
print(f"      • FAITS: {nb_faits} sous-section(s)")
print(f"      • PROCÉDURE: {nb_procedure} sous-section(s)")
print(f"      • MOYENS: {nb_moyens} sous-section(s)")
print(f"      • PRÉTENTIONS: {nb_pretentions} sous-section(s)")

# ========================================================================
# ÉTAPE 3 : Réduction des sections volumineuses (> 10000 tokens)
# ========================================================================
print(f"\n✂️  Étape 3/4 : Réduction des sections > {THRESHOLD_TOKENS:,} tokens...")

sections_reduites = []

for section_name in ["faits", "procedure", "moyens", "pretentions"]:
    if section_name not in structure:
        continue

    if "sous_sections" not in structure[section_name]:
        continue

    for i, subsection in enumerate(structure[section_name]["sous_sections"]):
        contenu = subsection.get("contenu", "")
        tokens = estimate_tokens(contenu)
        titre = subsection.get("titre", f"Sous-section {i+1}")

        if tokens > THRESHOLD_TOKENS:
            print(f"\n   📝 Réduction de [{section_name}] '{titre[:60]}...'")
            print(f"      Tokens original: {tokens:,}")
            print(f"      Tokens cible: ~{int(tokens * (1 - REDUCTION_PCT/100)):,} (-{REDUCTION_PCT}%)")

            # Réduire la sous-section
            reduced_content = reduce_subsection(contenu, api_key, REDUCTION_PCT)
            subsection["contenu"] = reduced_content

            tokens_reduit = estimate_tokens(reduced_content)
            print(f"      Tokens obtenu: {tokens_reduit:,} (-{100*(1-tokens_reduit/tokens):.1f}%)")

            sections_reduites.append({
                "section": section_name,
                "titre": titre,
                "tokens_original": tokens,
                "tokens_reduit": tokens_reduit,
                "reduction_pct": 100 * (1 - tokens_reduit/tokens)
            })

if not sections_reduites:
    print(f"\n   ℹ️  Aucune section > {THRESHOLD_TOKENS:,} tokens détectée")
else:
    print(f"\n   ✅ {len(sections_reduites)} section(s) réduite(s)")

# ========================================================================
# ÉTAPE 4 : Reconstitution du document
# ========================================================================
print("\n🔧 Étape 4/4 : Reconstitution du document...")

reconstructed_doc = reconstruct_document(structure)
tokens_reconstitue = estimate_tokens(reconstructed_doc)

print(f"   ✅ Document reconstitué: {len(reconstructed_doc):,} caractères, ~{tokens_reconstitue:,} tokens")

# ========================================================================
# SAUVEGARDE
# ========================================================================
output_file = "dossier_6_compresse_reconstruit.txt"

with open(output_file, "w", encoding="utf-8") as f:
    f.write(reconstructed_doc)

print(f"\n💾 Document sauvegardé: {output_file}")

# Sauvegarder les métadonnées
metadata = {
    "configuration": {
        "threshold_tokens": THRESHOLD_TOKENS,
        "reduction_pct": REDUCTION_PCT
    },
    "tokens": {
        "original": tokens_original,
        "reconstitue": tokens_reconstitue,
        "reduction_globale_pct": round(100 * (1 - tokens_reconstitue/tokens_original), 2)
    },
    "structure": {
        "nb_faits": nb_faits,
        "nb_procedure": nb_procedure,
        "nb_moyens": nb_moyens,
        "nb_pretentions": nb_pretentions
    },
    "sections_reduites": sections_reduites
}

metadata_file = "dossier_6_compression_metadata.json"
with open(metadata_file, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print(f"📊 Métadonnées sauvegardées: {metadata_file}")

# ========================================================================
# RÉCAPITULATIF
# ========================================================================
print("\n" + "="*80)
print("📊 RÉCAPITULATIF")
print("="*80)
print(f"\n📄 Tokens:")
print(f"   • Original: {tokens_original:,} tokens")
print(f"   • Reconstitué: {tokens_reconstitue:,} tokens")
print(f"   • Réduction globale: -{100 * (1 - tokens_reconstitue/tokens_original):.1f}%")

print(f"\n✂️  Sections réduites:")
if sections_reduites:
    for sr in sections_reduites:
        print(f"   • [{sr['section']:12s}] {sr['titre'][:50]:50s} | {sr['tokens_original']:6,} → {sr['tokens_reduit']:6,} tokens (-{sr['reduction_pct']:.1f}%)")
else:
    print(f"   • Aucune section réduite")

print(f"\n✅ Pipeline terminé avec succès!")
print("="*80)
