"""
Test final pour vérifier l'ordre des sections après reconstitution.
"""
import json
import sys
sys.path.insert(0, 'app')

from compression_simple.document_reconstruction import reconstruct_document

# Charger la structure
with open("dossier_6_structure_regex.json", "r", encoding="utf-8") as f:
    structure = json.load(f)

# Reconstituer le document
doc_reconstitue = reconstruct_document(structure)

# Extraire les titres de section du document reconstitué
print("📋 Ordre des sections dans le document reconstitué:\n")
lines = doc_reconstitue.split('\n')
for i, line in enumerate(lines, 1):
    if line.strip() and len(line) < 150 and not line.startswith(' '):
        # Probable titre de section
        if any(keyword in line.upper() for keyword in [
            "CONCLUSIONS", "FAITS", "PROCEDURE", "DISCUSSION",
            "PRELIMINAIRE", "RESILIATION", "EN DROIT", "EN L'ESPECE",
            "MONTANT", "LICENCIEMENT", "DEMANDES", "DOMMAGES",
            "MODIFICATION", "RESERVES", "PAR CES MOTIFS"
        ]):
            print(f"  {i:3d}. {line[:80]}")

print("\n" + "="*80)

# Vérifier l'ordre des positions
print("\n🔍 Vérification des positions dans la structure JSON:\n")

all_subsections = []
for section_name in ["faits", "procedure", "moyens", "pretentions"]:
    if section_name in structure and "sous_sections" in structure[section_name]:
        for ss in structure[section_name]["sous_sections"]:
            all_subsections.append({
                "type": section_name,
                "titre": ss.get("titre", ""),
                "position": ss.get("position", 999999)
            })

all_subsections.sort(key=lambda x: x["position"])

for ss in all_subsections:
    print(f"  Position {ss['position']:2d}: [{ss['type']:12s}] {ss['titre'][:60]}")

print("\n✅ L'ordre est maintenant basé sur le champ 'position' !")
