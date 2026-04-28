"""
Script de vérification de la structure générée.
"""
import json

with open("dossier_6_structure_regex.json", "r", encoding="utf-8") as f:
    structure = json.load(f)

print("✅ Fichier dossier_6_structure_regex.json régénéré\n")
print("="*80)
print("\n📋 Ordre des sections (triées par position):\n")

# Collecter toutes les sous-sections
all_subsections = []
for section_name in ["faits", "procedure", "moyens", "pretentions"]:
    if section_name in structure and "sous_sections" in structure[section_name]:
        for ss in structure[section_name]["sous_sections"]:
            all_subsections.append({
                "position": ss.get("position", 999999),
                "type": ss.get("type", "unknown"),
                "titre": ss.get("titre", ""),
                "tokens": ss.get("tokens", 0)
            })

# Trier par position
all_subsections.sort(key=lambda x: x["position"])

# Afficher
for ss in all_subsections:
    print(f"  Position {ss['position']:2d}: [{ss['type']:12s}] {ss['tokens']:6,} tokens | {ss['titre'][:60]}")

print("\n" + "="*80)
print("\n📊 Récapitulatif:\n")
print(f"  • Total: {len(all_subsections)} sections détectées")
print(f"  • FAITS: {len(structure.get('faits', {}).get('sous_sections', []))} sous-section(s)")
print(f"  • PROCÉDURE: {len(structure.get('procedure', {}).get('sous_sections', []))} sous-section(s)")
print(f"  • MOYENS: {len(structure.get('moyens', {}).get('sous_sections', []))} sous-section(s)")
print(f"  • PRÉTENTIONS: {len(structure.get('pretentions', {}).get('sous_sections', []))} sous-section(s)")

print("\n✅ Vérifications:")
print(f"  • Champ 'position' présent: {all(ss['position'] != 999999 for ss in all_subsections)}")
print(f"  • Champ 'type' présent: {all(ss['type'] != 'unknown' for ss in all_subsections)}")
print(f"  • Ordre séquentiel: {[ss['position'] for ss in all_subsections] == list(range(1, len(all_subsections) + 1))}")
