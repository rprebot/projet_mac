"""
Test pour vérifier si l'ordre des sections est préservé lors de la reconstitution.
"""
import json
import sys
sys.path.insert(0, 'app')

from compression_simple.document_reconstruction import reconstruct_document

# Charger la structure
with open("dossier_6_structure_regex.json", "r", encoding="utf-8") as f:
    structure = json.load(f)

print("📄 Document original - Ordre d'apparition des sections:\n")

# Lire le document original pour voir l'ordre réel
with open("app/dossiers/Dossier_6_conclusion_appelant.txt", "r", encoding="utf-8") as f:
    doc_original = f.read()

# Extraire les premiers titres de sections du document original
import re
lines = doc_original.split('\n')[:200]  # Regarder les 200 premières lignes
for i, line in enumerate(lines):
    line = line.strip()
    if any(keyword in line.upper() for keyword in ["CONCLUSIONS D'APPELANT", "I. LES FAITS", "II. LA PROCEDURE", "DISCUSSION"]):
        if len(line) > 0 and len(line) < 150:
            print(f"  Ligne {i+1}: {line[:80]}")

print("\n" + "="*80 + "\n")

print("📦 Structure JSON - Ordre de classification:\n")

for section_name in ["faits", "procedure", "moyens", "pretentions"]:
    if section_name in structure:
        section = structure[section_name]
        print(f"  {section_name.upper()}:")

        if "sous_sections" in section:
            for i, ss in enumerate(section["sous_sections"][:5], 1):  # Montrer les 5 premières
                titre = ss.get("titre", "Sans titre")
                print(f"    {i}. {titre[:70]}")
            if len(section["sous_sections"]) > 5:
                print(f"    ... ({len(section['sous_sections']) - 5} autres)")
        elif "contenu" in section:
            preview = section["contenu"][:80].replace("\n", " ")
            print(f"    {preview}...")
        print()

print("="*80 + "\n")

print("🔧 Document reconstitué - Ordre après reconstitution:\n")

# Reconstituer le document
doc_reconstitue = reconstruct_document(structure)

# Montrer les premières lignes du document reconstitué
lines = doc_reconstitue.split('\n')[:50]
for line in lines:
    if line.strip() and (line.startswith('#') or 'CONCLUSIONS' in line or 'DISCUSSION' in line):
        print(f"  {line[:80]}")

print("\n" + "="*80)
print("\n⚠️  ANALYSE:")
print("\nDans le document ORIGINAL:")
print("  1. CONCLUSIONS D'APPELANT")
print("  2. I. LES FAITS")
print("  3. II. LA PROCEDURE")
print("  4. DISCUSSION")
print("\nDans le document RECONSTITUÉ:")
print("  1. # FAITS")
print("  2. ## I. LES FAITS")
print("  3. # PROCÉDURE")
print("  4. ## II. LA PROCEDURE")
print("  5. # MOYENS")
print("  6. ## CONCLUSIONS D'APPELANT  ⬅️ DÉPLACÉ ICI!")
print("  7. ## DISCUSSION")
print("\n❌ L'ordre n'est PAS préservé! Les sections sont réorganisées par catégorie.")
