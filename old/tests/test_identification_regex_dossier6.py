"""
Test de l'identification de structure regex sur le dossier 6 appelant.
"""
import json
import sys
sys.path.insert(0, 'app')

from compression_simple.structure_identification import identify_structure_regex

# Lire le document
with open("app/dossiers/Dossier_6_conclusion_appelant.txt", "r", encoding="utf-8") as f:
    document = f.read()

print("📄 Document chargé")
print(f"   Longueur: {len(document):,} caractères")
print()

# Identifier la structure
print("🔍 Identification de la structure (regex)...")
structure = identify_structure_regex(document)

# Afficher les statistiques
print("\n📊 Statistiques de la structure détectée:\n")

for section_name in ["faits", "procedure", "moyens", "pretentions"]:
    if section_name in structure:
        section = structure[section_name]

        if "sous_sections" in section:
            nb_sous_sections = len(section["sous_sections"])
            total_tokens = sum(ss.get("tokens", 0) for ss in section["sous_sections"])
            print(f"  {section_name.upper()}: {nb_sous_sections} sous-sections, {total_tokens:,} tokens")

            for i, ss in enumerate(section["sous_sections"], 1):
                titre = ss.get("titre", "Sans titre")
                tokens = ss.get("tokens", 0)
                print(f"    {i}. {titre[:60]}... ({tokens:,} tokens)")

        elif "contenu" in section:
            tokens = section.get("tokens", 0)
            preview = section["contenu"][:100].replace("\n", " ")
            print(f"  {section_name.upper()}: {tokens:,} tokens")
            print(f"    Aperçu: {preview}...")

# Sauvegarder le résultat
output_file = "dossier_6_structure_regex.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(structure, f, ensure_ascii=False, indent=2)

print(f"\n✅ Structure sauvegardée dans: {output_file}")
