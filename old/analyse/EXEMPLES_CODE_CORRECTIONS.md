# EXEMPLES DE CODE - CORRECTIONS PIPELINE DOSSIER 6

Ce document fournit des exemples de code prêts à l'emploi pour implémenter les corrections prioritaires identifiées dans l'analyse du dossier 6.

---

## 1. PROMPT EXPLICITE POUR GRIEFS NUMÉROTÉS

### Amélioration du prompt système

```python
SYSTEM_PROMPT_ENHANCED = """
Vous êtes un assistant juridique expert spécialisé dans l'extraction structurée de conclusions juridiques.

CONSIGNE CRITIQUE : EXTRACTION DES GRIEFS NUMÉROTÉS

Si le document contient des griefs ou arguments numérotés (exemples de formats possibles) :
- GRIEF 1, GRIEF 2, ..., GRIEF N
- MOYEN 1, MOYEN 2, ..., MOYEN N
- ARGUMENT 1, ARGUMENT 2, ..., ARGUMENT N
- 1°), 2°), 3°), ...

Vous DEVEZ extraire CHAQUE grief/moyen/argument dans une section JSON distincte.

RÈGLES ABSOLUES :
1. NE JAMAIS omettre de griefs (même s'ils semblent répétitifs)
2. NE JAMAIS agréger plusieurs griefs en une seule section
3. TOUJOURS vérifier que le nombre de sections extraites = nombre de griefs dans l'original

FORMAT ATTENDU pour chaque grief :

{
  "title": "GRIEF X : [résumé en 5-10 mots]",
  "section_type": "sub-argument",
  "path": ["Section parente", "Sous-section", "GRIEF X"],
  "participants": [...],
  "thesis": "[Thèse du grief en 1-2 phrases]",
  "facts": [
    "[Fait 1 spécifique au grief]",
    "[Fait 2]",
    ...
  ],
  "arguments": [
    "[Argument 1 : allégation du salarié OU réfutation de l'employeur]",
    "[Argument 2]",
    ...
  ],
  "rebuttals": [
    "[Si grief réfuté : argument de réfutation]",
    ...
  ],
  "legal_references": ["[Article ou jurisprudence citée]", ...],
  "pieces_cited": ["pièce X", "pièce Y", ...],
  "dates_amounts": ["[Dates et montants mentionnés]", ...],
  "key_source_excerpt": "« [Extrait verbatim de 100-200 mots du grief original] »",
  "key_verbatim_points": [
    "« [Citation exacte 1 : phrase clé du grief] »",
    "« [Citation exacte 2] »"
  ],
  "compression_ratio_hint": "low|medium|high",
  "importance": "low|medium|high",
  "argument_density": "low|medium|high"
}

EXEMPLE CONCRET :

Si vous lisez :
```
GRIEF 5 : Sur la modification unilatérale de l'organisation du travail

Attendu que le 6 avril 2020, M. [G] a reçu par courriel les modalités
d'organisation de son travail dans le cadre de l'activité partielle,
ce document mentionnant « congés à ta demande » à 2 reprises.
```

Vous devez produire :
```json
{
  "title": "GRIEF 5 : Modification unilatérale organisation travail",
  "section_type": "sub-argument",
  "path": ["I- SUR LA DEMANDE DE RESILIATION", "A- ABSENCE DE MANQUEMENTS", "2- EN L'ESPECE", "GRIEF 5"],
  "facts": [
    "06/04/2020 : M. [G] reçoit par courriel modalités organisation travail (activité partielle)",
    "Document mentionne 'congés à ta demande' (2 fois)"
  ],
  "arguments": [
    "La modification unilatérale des modalités d'organisation constitue un manquement grave."
  ],
  "dates_amounts": ["06 avril 2020"],
  "key_source_excerpt": "« Attendu que le 6 avril 2020, M. [G] a reçu par courriel les modalités d'organisation de son travail dans le cadre de l'activité partielle, ce document mentionnant « congés à ta demande » à 2 reprises. »",
  "key_verbatim_points": [
    "« congés à ta demande » (mentionné 2 fois)"
  ]
}
```

AUTO-VÉRIFICATION OBLIGATOIRE :
Avant de finaliser votre extraction, comptez :
- Nombre de griefs détectés dans le document original : [X]
- Nombre de sections JSON de type "sub-argument" créées : [Y]
- Si X ≠ Y : ERREUR, reprenez l'extraction

[... reste du prompt système ...]
"""
```

---

## 2. VALIDATION AUTOMATIQUE DE COMPLÉTUDE

### Script de validation post-compression

```python
import re
import json
from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class ValidationReport:
    valid: bool
    errors: List[Dict]
    warnings: List[Dict]
    metrics: Dict

def validate_compression(
    original_appelant_text: str,
    original_intimé_text: str,
    json_compressed: List[Dict]
) -> ValidationReport:
    """
    Valide que la compression JSON n'a pas perdu d'information critique.

    Args:
        original_appelant_text: Texte de la conclusion de l'appelant
        original_intimé_text: Texte de la conclusion de l'intimé
        json_compressed: Liste des packets JSON compressés

    Returns:
        ValidationReport avec erreurs, warnings et métriques
    """
    report = ValidationReport(
        valid=True,
        errors=[],
        warnings=[],
        metrics={}
    )

    original_text = original_appelant_text + "\n" + original_intimé_text

    # ===================================================================
    # CHECK 1 : GRIEFS NUMÉROTÉS
    # ===================================================================

    # Détection des griefs dans l'original
    original_griefs = set(re.findall(r'GRIEF\s+(\d+)\s*:', original_text, re.IGNORECASE))

    # Extraction des griefs du JSON
    json_griefs = set()
    for packet in json_compressed:
        for section in packet.get('sections', []):
            title = section.get('title', '')
            match = re.search(r'GRIEF\s+(\d+)', title, re.IGNORECASE)
            if match:
                json_griefs.add(match.group(1))

    missing_griefs = original_griefs - json_griefs

    if missing_griefs:
        report.errors.append({
            "type": "grief_count_mismatch",
            "severity": "critical",
            "original_count": len(original_griefs),
            "json_count": len(json_griefs),
            "missing_griefs": sorted(missing_griefs, key=int),
            "message": f"🔴 {len(missing_griefs)} griefs manquants : GRIEF {', '.join(sorted(missing_griefs, key=int))}"
        })
        report.valid = False

    report.metrics['griefs_original'] = len(original_griefs)
    report.metrics['griefs_json'] = len(json_griefs)
    report.metrics['griefs_completeness'] = len(json_griefs) / len(original_griefs) if original_griefs else 1.0

    # ===================================================================
    # CHECK 2 : MONTANTS CHIFFRÉS
    # ===================================================================

    # Détection des montants dans l'original (formats : 123,45 € ou 123.45 € ou 123 €)
    original_amounts_raw = re.findall(
        r'(\d[\d\s,\.]*)\s*(?:€|euros?)',
        original_text,
        re.IGNORECASE
    )
    original_amounts = set([
        amt.replace(' ', '').replace(',', '.').strip()
        for amt in original_amounts_raw
        if len(amt.replace(' ', '').replace(',', '').replace('.', '')) >= 2  # Au moins 2 chiffres
    ])

    # Extraction des montants du JSON
    json_amounts = set()
    for packet in json_compressed:
        for section in packet.get('sections', []):
            # Chercher dans dates_amounts
            for item in section.get('dates_amounts', []):
                amounts = re.findall(r'(\d[\d\s,\.]*)\s*€', item)
                json_amounts.update([
                    amt.replace(' ', '').replace(',', '.').strip()
                    for amt in amounts
                ])

            # Chercher dans requests
            for req in section.get('requests', []):
                if isinstance(req, str):
                    amounts = re.findall(r'(\d[\d\s,\.]*)\s*€', req)
                    json_amounts.update([
                        amt.replace(' ', '').replace(',', '.').strip()
                        for amt in amounts
                    ])

    missing_amounts = original_amounts - json_amounts
    missing_percentage = len(missing_amounts) / len(original_amounts) * 100 if original_amounts else 0

    if missing_percentage > 10:  # Seuil : >10% de montants manquants
        report.warnings.append({
            "type": "amounts_missing",
            "severity": "high" if missing_percentage > 30 else "medium",
            "original_count": len(original_amounts),
            "json_count": len(json_amounts),
            "missing_count": len(missing_amounts),
            "missing_percentage": round(missing_percentage, 2),
            "examples": list(missing_amounts)[:10],
            "message": f"⚠️  {missing_percentage:.1f}% des montants manquants ({len(missing_amounts)}/{len(original_amounts)})"
        })

    report.metrics['amounts_original'] = len(original_amounts)
    report.metrics['amounts_json'] = len(json_amounts)
    report.metrics['amounts_completeness'] = len(json_amounts) / len(original_amounts) if original_amounts else 1.0

    # ===================================================================
    # CHECK 3 : SECTIONS "PAR CES MOTIFS"
    # ===================================================================

    original_par_ces_motifs = len(re.findall(r'PAR CES MOTIF', original_text, re.IGNORECASE))

    json_par_ces_motifs = sum([
        1 for packet in json_compressed
        for section in packet.get('sections', [])
        if 'PAR CES MOTIF' in section.get('title', '').upper()
    ])

    if original_par_ces_motifs != json_par_ces_motifs:
        report.errors.append({
            "type": "par_ces_motifs_missing",
            "severity": "critical",
            "original_count": original_par_ces_motifs,
            "json_count": json_par_ces_motifs,
            "message": f"🔴 {original_par_ces_motifs - json_par_ces_motifs} section(s) 'PAR CES MOTIFS' manquante(s)"
        })
        report.valid = False

    # ===================================================================
    # CHECK 4 : JURISPRUDENCE
    # ===================================================================

    original_cass = set(re.findall(
        r'Cass\.\s+\w+\.?\s+\d+\s+\w+\.?\s+\d{4},?\s+n[°o]\s*[\d\-]+',
        original_text,
        re.IGNORECASE
    ))

    json_cass = set()
    for packet in json_compressed:
        for section in packet.get('sections', []):
            for ref in section.get('legal_references', []):
                cass_match = re.search(
                    r'Cass\.\s+\w+\.?\s+\d+\s+\w+\.?\s+\d{4},?\s+n[°o]\s*[\d\-]+',
                    ref,
                    re.IGNORECASE
                )
                if cass_match:
                    json_cass.add(cass_match.group(0))

    missing_cass = original_cass - json_cass
    missing_cass_percentage = len(missing_cass) / len(original_cass) * 100 if original_cass else 0

    if missing_cass_percentage > 20:  # Seuil : >20% de jurisprudence manquante
        report.warnings.append({
            "type": "jurisprudence_missing",
            "severity": "medium",
            "original_count": len(original_cass),
            "json_count": len(json_cass),
            "missing_count": len(missing_cass),
            "missing_percentage": round(missing_cass_percentage, 2),
            "examples": list(missing_cass)[:5],
            "message": f"⚠️  {missing_cass_percentage:.1f}% de la jurisprudence manquante"
        })

    report.metrics['jurisprudence_original'] = len(original_cass)
    report.metrics['jurisprudence_json'] = len(json_cass)
    report.metrics['jurisprudence_completeness'] = len(json_cass) / len(original_cass) if original_cass else 1.0

    # ===================================================================
    # CHECK 5 : ÉQUILIBRE APPELANT / INTIMÉ
    # ===================================================================

    packets_appelant = [p for p in json_compressed if p.get('document_role') == 'appelant']
    packets_intimé = [p for p in json_compressed if p.get('document_role') == 'intimé']

    # Calculer le ratio de lignes original vs nombre de packets
    original_appelant_lines = len(original_appelant_text.split('\n'))
    original_intimé_lines = len(original_intimé_text.split('\n'))

    ratio_appelant = original_appelant_lines / len(packets_appelant) if packets_appelant else 0
    ratio_intimé = original_intimé_lines / len(packets_intimé) if packets_intimé else float('inf')

    if ratio_intimé / ratio_appelant > 2:  # Déséquilibre >2x
        report.warnings.append({
            "type": "imbalance_appelant_intimé",
            "severity": "medium",
            "appelant_packets": len(packets_appelant),
            "intimé_packets": len(packets_intimé),
            "appelant_lines": original_appelant_lines,
            "intimé_lines": original_intimé_lines,
            "ratio_imbalance": round(ratio_intimé / ratio_appelant, 2),
            "message": f"⚠️  Déséquilibre appelant/intimé : {len(packets_appelant)} vs {len(packets_intimé)} packets (ratio {ratio_intimé/ratio_appelant:.1f}x)"
        })

    # ===================================================================
    # SCORE GLOBAL
    # ===================================================================

    completeness_scores = [
        report.metrics.get('griefs_completeness', 1.0),
        report.metrics.get('amounts_completeness', 1.0),
        report.metrics.get('jurisprudence_completeness', 1.0)
    ]

    report.metrics['global_completeness_score'] = sum(completeness_scores) / len(completeness_scores)

    return report

# ===================================================================
# UTILISATION
# ===================================================================

def main():
    # Charger les documents
    with open('/path/to/Dossier_6_conclusion_appelant.txt', 'r', encoding='utf-8') as f:
        original_appelant = f.read()

    with open('/path/to/Dossier_6_conclusion_intimee.txt', 'r', encoding='utf-8') as f:
        original_intimé = f.read()

    with open('/path/to/dossier_6_compresse.json', 'r', encoding='utf-8') as f:
        json_compressed = json.load(f)

    # Valider
    report = validate_compression(original_appelant, original_intimé, json_compressed)

    # Afficher le rapport
    print("=" * 80)
    print("RAPPORT DE VALIDATION DE COMPRESSION")
    print("=" * 80)

    if report.valid:
        print("✅ COMPRESSION VALIDE")
    else:
        print("❌ COMPRESSION INVALIDE - ERREURS CRITIQUES DÉTECTÉES")

    print(f"\n📊 SCORE GLOBAL DE COMPLÉTUDE : {report.metrics['global_completeness_score']:.1%}")

    if report.errors:
        print("\n🔴 ERREURS CRITIQUES :")
        for error in report.errors:
            print(f"  - {error['message']}")
            if 'missing_griefs' in error:
                print(f"    Détail : Griefs manquants = {error['missing_griefs']}")

    if report.warnings:
        print("\n⚠️  WARNINGS :")
        for warning in report.warnings:
            print(f"  - {warning['message']}")
            if 'examples' in warning and warning['examples']:
                print(f"    Exemples : {warning['examples'][:3]}")

    print("\n📈 MÉTRIQUES DÉTAILLÉES :")
    print(f"  - Griefs : {report.metrics['griefs_json']}/{report.metrics['griefs_original']} ({report.metrics['griefs_completeness']:.1%})")
    print(f"  - Montants : {report.metrics['amounts_json']}/{report.metrics['amounts_original']} ({report.metrics['amounts_completeness']:.1%})")
    print(f"  - Jurisprudence : {report.metrics['jurisprudence_json']}/{report.metrics['jurisprudence_original']} ({report.metrics['jurisprudence_completeness']:.1%})")

    # Décision
    if not report.valid:
        print("\n⛔ DÉCISION : REJETER LA COMPRESSION, REDEMANDER L'EXTRACTION AU LLM")
        return False
    elif report.metrics['global_completeness_score'] < 0.70:
        print("\n⚠️  DÉCISION : COMPRESSION ACCEPTABLE MAIS PERFECTIBLE (score < 70%)")
        print("    Recommandation : Améliorer le prompt d'extraction")
        return True
    else:
        print("\n✅ DÉCISION : COMPRESSION DE BONNE QUALITÉ (score ≥ 70%)")
        return True

if __name__ == "__main__":
    main()
```

---

## 3. HIÉRARCHISATION DES DEMANDES (PRINCIPAL/SUBSIDIAIRE)

### Amélioration du schéma JSON pour les sections "claims"

```python
# Schéma JSON enrichi pour les sections de type "claims"

CLAIMS_SCHEMA = {
    "title": str,
    "path": List[str],
    "section_type": "claims",
    "participants": List[Dict],
    "thesis": str,

    # NOUVEAU : Champ structuré pour hiérarchie des demandes
    "requests_hierarchy": [
        {
            "level": "principal",  # ou "subsidiaire", "infiniment_subsidiaire", "en_tout_état_de_cause"
            "label": str,  # ex: "À titre principal", "Subsidiairement", etc.
            "requests": [
                {
                    "description": str,
                    "amount": Optional[str],
                    "legal_basis": Optional[str],
                    "sub_requests": Optional[List[Dict]]  # Pour demandes imbriquées
                }
            ]
        }
    ],

    # Conservé pour rétrocompatibilité (mais deprecié)
    "requests": List[str],

    # Autres champs standards
    "legal_references": List[str],
    "dates_amounts": List[str],
    "key_source_excerpt": str,
    "key_verbatim_points": List[str],
    "compression_ratio_hint": str,
    "importance": str,
    "argument_density": str
}
```

### Prompt enrichi pour extraction des demandes

```python
PROMPT_CLAIMS_EXTRACTION = """
CONSIGNE CRITIQUE : EXTRACTION DES DEMANDES HIÉRARCHISÉES

Lorsque vous extrayez une section de type "claims" (PAR CES MOTIFS, PRÉTENTIONS, DEMANDES),
vous DEVEZ détecter et préserver la hiérarchie des demandes.

INDICATEURS DE HIÉRARCHIE À DÉTECTER :

1. "À titre principal" / "Principalement"
   → level: "principal"

2. "Subsidiairement" / "À titre subsidiaire" / "À défaut"
   → level: "subsidiaire"

3. "À titre infiniment subsidiaire" / "Plus subsidiairement encore"
   → level: "infiniment_subsidiaire"

4. "En tout état de cause" / "Dans tous les cas"
   → level: "en_tout_état_de_cause"

FORMAT ATTENDU :

Si vous lisez :
```
PAR CES MOTIFS

À titre principal,

Confirmer le jugement du CPH du 5 avril 2024 en toutes ses dispositions.

Condamner l'Association à payer 3.600 € au titre de l'article 700 du CPC.

Subsidiairement, en cas d'infirmation,

Prononcer la résiliation judiciaire du contrat aux torts de l'employeur.

Condamner l'Association à payer :
- 186,07 € (régularisation salaire)
- 18,61 € (CP sur régularisation)
- 3.239,75 € (solde CP)
- 19.030,20 € (D&I harcèlement)

En tout état de cause,

Condamner l'Association aux entiers dépens.
```

Vous DEVEZ produire :
```json
{
  "title": "PAR CES MOTIFS",
  "section_type": "claims",
  "requests_hierarchy": [
    {
      "level": "principal",
      "label": "À titre principal",
      "requests": [
        {
          "description": "Confirmer le jugement du Conseil des Prud'hommes de [Localité] du 5 avril 2024 en toutes ses dispositions.",
          "amount": null,
          "legal_basis": null
        },
        {
          "description": "Condamner l'Association [Personne Morale 1] à payer à Monsieur [B] [A] une indemnité au titre de l'article 700 du Code de Procédure Civile.",
          "amount": "3.600 €",
          "legal_basis": "Article 700 du Code de Procédure Civile"
        }
      ]
    },
    {
      "level": "subsidiaire",
      "label": "Subsidiairement, en cas d'infirmation",
      "requests": [
        {
          "description": "Prononcer la résiliation judiciaire du contrat de travail aux torts et griefs de l'Association [Personne Morale 1].",
          "amount": null,
          "legal_basis": null
        },
        {
          "description": "Condamner l'Association [Personne Morale 1] à payer à Monsieur [B] [A] :",
          "amount": null,
          "legal_basis": null,
          "sub_requests": [
            {
              "description": "Régularisation du salaire de base de mai 2022 à septembre 2022",
              "amount": "186,07 €",
              "legal_basis": null
            },
            {
              "description": "Indemnité compensatrice de congés payés sur régularisation",
              "amount": "18,61 €",
              "legal_basis": "Article L 3141-22 du Code du Travail"
            },
            {
              "description": "Solde de l'indemnité compensatrice de congés payés",
              "amount": "3.239,75 €",
              "legal_basis": null
            },
            {
              "description": "Dommages-intérêts en réparation du harcèlement moral subi",
              "amount": "19.030,20 €",
              "legal_basis": "Article L 1152-1 du Code du Travail"
            }
          ]
        }
      ]
    },
    {
      "level": "en_tout_état_de_cause",
      "label": "En tout état de cause",
      "requests": [
        {
          "description": "Condamner l'Association [Personne Morale 1] aux entiers dépens de l'instance.",
          "amount": null,
          "legal_basis": "Article 696 du Code de Procédure Civile"
        }
      ]
    }
  ],

  "requests": [
    "Confirmer le jugement du CPH du 5 avril 2024 en toutes ses dispositions.",
    "Condamner l'Association à payer 3.600 € (art. 700 CPC)",
    "Subsidiairement : Résiliation judiciaire aux torts employeur",
    "Subsidiairement : Condamner à payer 186,07 € + 18,61 € + 3.239,75 € + 19.030,20 €",
    "En tout état de cause : Condamner aux entiers dépens"
  ],

  "dates_amounts": [
    "5 avril 2024",
    "3.600 €",
    "186,07 €",
    "18,61 €",
    "3.239,75 €",
    "19.030,20 €"
  ],

  "legal_references": [
    "Article 700 du Code de Procédure Civile",
    "Article L 3141-22 du Code du Travail",
    "Article L 1152-1 du Code du Travail",
    "Article 696 du Code de Procédure Civile"
  ]
}
```

RÈGLES ABSOLUES :
1. NE JAMAIS utiliser "etc." pour agréger des montants
2. TOUJOURS décomposer les listes de montants en sub_requests
3. TOUJOURS préserver l'ordre hiérarchique (principal → subsidiaire → infiniment subsidiaire → en tout état de cause)
4. TOUJOURS extraire CHAQUE montant avec son libellé exact
"""
```

---

## 4. DÉTECTION AUTOMATIQUE DE STRUCTURE (MAPPAGE PRÉ-EXTRACTION)

```python
import re
from typing import Dict, List, Tuple

def map_document_structure(text: str) -> Dict:
    """
    Détecte la structure hiérarchique du document avant extraction.
    Permet au LLM de savoir combien de griefs/moyens il doit extraire.

    Returns:
        Dict avec la structure détectée et des statistiques
    """
    structure = {
        "sections": [],
        "hierarchy_levels": {},
        "auto_check_instructions": ""
    }

    # ===================================================================
    # NIVEAU 1 : SECTIONS PRINCIPALES (I-, II-, III-, IV-, ...)
    # ===================================================================
    level1_pattern = r'^([IVX]+)-\s+(.+?)$'
    level1_matches = re.findall(level1_pattern, text, re.MULTILINE)

    structure['hierarchy_levels']['level1'] = {
        'count': len(level1_matches),
        'pattern': 'I-, II-, III-, ...',
        'sections': [f"{num}- {title}" for num, title in level1_matches]
    }

    # ===================================================================
    # NIVEAU 2 : SOUS-SECTIONS (A-, B-, C-, ...)
    # ===================================================================
    level2_pattern = r'^([A-Z])-\s+(.+?)$'
    level2_matches = re.findall(level2_pattern, text, re.MULTILINE)

    structure['hierarchy_levels']['level2'] = {
        'count': len(level2_matches),
        'pattern': 'A-, B-, C-, ...',
        'sections': [f"{letter}- {title}" for letter, title in level2_matches]
    }

    # ===================================================================
    # NIVEAU 3 : SOUS-SOUS-SECTIONS (1-, 2-, 3-, ...)
    # ===================================================================
    level3_pattern = r'^(\d+)-\s+(.+?)$'
    level3_matches = re.findall(level3_pattern, text, re.MULTILINE)

    structure['hierarchy_levels']['level3'] = {
        'count': len(level3_matches),
        'pattern': '1-, 2-, 3-, ...',
        'sections': [f"{num}- {title}" for num, title in level3_matches]
    }

    # ===================================================================
    # NIVEAU 4 : GRIEFS / MOYENS NUMÉROTÉS
    # ===================================================================

    # Recherche de différents formats possibles
    patterns = {
        'GRIEF X :': r'GRIEF\s+(\d+)\s*:',
        'MOYEN X :': r'MOYEN\s+(\d+)\s*:',
        'ARGUMENT X :': r'ARGUMENT\s+(\d+)\s*:',
        'X°)': r'(\d+)°\)',
    }

    detected_pattern = None
    level4_matches = []

    for pattern_name, pattern_regex in patterns.items():
        matches = re.findall(pattern_regex, text, re.IGNORECASE)
        if len(matches) > len(level4_matches):
            detected_pattern = pattern_name
            level4_matches = matches

    structure['hierarchy_levels']['level4'] = {
        'count': len(level4_matches),
        'pattern': detected_pattern,
        'list': sorted(set(level4_matches), key=int),
        'min': int(min(level4_matches)) if level4_matches else None,
        'max': int(max(level4_matches)) if level4_matches else None,
        'gaps': []
    }

    # Détection de trous dans la numérotation
    if level4_matches:
        nums = sorted([int(x) for x in set(level4_matches)])
        for i in range(len(nums) - 1):
            if nums[i+1] - nums[i] > 1:
                structure['hierarchy_levels']['level4']['gaps'].append({
                    'after': nums[i],
                    'before': nums[i+1],
                    'missing': list(range(nums[i]+1, nums[i+1]))
                })

    # ===================================================================
    # GÉNÉRATION DES INSTRUCTIONS D'AUTO-VÉRIFICATION
    # ===================================================================

    instructions = f"""
AUTO-VÉRIFICATION OBLIGATOIRE POUR VOTRE EXTRACTION :

Le document source contient la structure hiérarchique suivante :

1. SECTIONS PRINCIPALES (niveau I-, II-, III-, ...) : {structure['hierarchy_levels']['level1']['count']} sections
   {chr(10).join([f"   - {s}" for s in structure['hierarchy_levels']['level1']['sections'][:5]])}
   {'   [...]' if len(structure['hierarchy_levels']['level1']['sections']) > 5 else ''}

2. SOUS-SECTIONS (niveau A-, B-, C-, ...) : {structure['hierarchy_levels']['level2']['count']} sous-sections

3. SOUS-SOUS-SECTIONS (niveau 1-, 2-, 3-, ...) : {structure['hierarchy_levels']['level3']['count']} sous-sous-sections

4. **GRIEFS/MOYENS NUMÉROTÉS (NIVEAU CRITIQUE)** : {structure['hierarchy_levels']['level4']['count']} éléments
   Format détecté : {structure['hierarchy_levels']['level4']['pattern']}
   Liste complète : {', '.join(structure['hierarchy_levels']['level4']['list'])}
   {f"   ⚠️  ATTENTION : Numérotation avec trous détectés : {structure['hierarchy_levels']['level4']['gaps']}" if structure['hierarchy_levels']['level4']['gaps'] else "   ✅ Numérotation continue"}

**CONSIGNE CRITIQUE** :
Vous DEVEZ extraire EXACTEMENT {structure['hierarchy_levels']['level4']['count']} sections de type "sub-argument"
correspondant aux {structure['hierarchy_levels']['level4']['count']} {detected_pattern} détectés.

AVANT DE FINALISER VOTRE EXTRACTION, VÉRIFIEZ :
☐ Nombre de sections "sub-argument" créées = {structure['hierarchy_levels']['level4']['count']}
☐ Liste des numéros extraits = {{{', '.join(structure['hierarchy_levels']['level4']['list'])}}}

Si ces conditions ne sont PAS remplies, REPRENEZ l'extraction intégralement.
"""

    structure['auto_check_instructions'] = instructions

    return structure

# ===================================================================
# UTILISATION DANS LE PIPELINE
# ===================================================================

def extract_with_structure_mapping(document_text: str, llm_client) -> Dict:
    """
    Pipeline d'extraction avec mappage de structure préalable.
    """

    # ÉTAPE 1 : Mapper la structure
    structure = map_document_structure(document_text)

    print("=" * 80)
    print("STRUCTURE DÉTECTÉE :")
    print("=" * 80)
    print(structure['auto_check_instructions'])
    print("=" * 80)

    # ÉTAPE 2 : Construire le prompt avec les instructions d'auto-vérification
    system_prompt = SYSTEM_PROMPT_ENHANCED  # Défini plus haut
    user_prompt = f"""
{structure['auto_check_instructions']}

Veuillez extraire le document suivant en JSON structuré, en respectant SCRUPULEUSEMENT
les consignes d'auto-vérification ci-dessus.

DOCUMENT À EXTRAIRE :
{document_text}
"""

    # ÉTAPE 3 : Appeler le LLM
    response = llm_client.chat.completions.create(
        model="claude-sonnet-4-5-20250929",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=16000,
        temperature=0.0
    )

    extracted_json = json.loads(response.choices[0].message.content)

    # ÉTAPE 4 : Vérification post-extraction
    extracted_griefs = [
        s['title'] for s in extracted_json.get('sections', [])
        if s.get('section_type') == 'sub-argument' and
        re.search(r'GRIEF\s+(\d+)', s['title'], re.IGNORECASE)
    ]

    expected_count = structure['hierarchy_levels']['level4']['count']
    actual_count = len(extracted_griefs)

    if expected_count != actual_count:
        print(f"❌ ERREUR : Nombre de griefs attendu ({expected_count}) ≠ extrait ({actual_count})")
        print(f"   Griefs extraits : {extracted_griefs}")
        print("   → REDEMANDER L'EXTRACTION AU LLM")
        return None
    else:
        print(f"✅ Vérification OK : {actual_count}/{expected_count} griefs extraits")
        return extracted_json

# Exemple d'utilisation
if __name__ == "__main__":
    with open('/path/to/Dossier_6_conclusion_appelant.txt', 'r', encoding='utf-8') as f:
        doc_text = f.read()

    # Simuler un client LLM (remplacer par votre client réel)
    class MockLLMClient:
        pass

    llm_client = MockLLMClient()

    extracted = extract_with_structure_mapping(doc_text, llm_client)

    if extracted:
        with open('dossier_6_compresse_v2.json', 'w', encoding='utf-8') as f:
            json.dump(extracted, f, ensure_ascii=False, indent=2)
        print("✅ Extraction réussie et sauvegardée dans dossier_6_compresse_v2.json")
```

---

## 5. PIPELINE EN 2 PASSES (EXTRACTION + COMPRESSION)

```python
from typing import Dict, List, Optional
import json

class TwoPassCompressionPipeline:
    """
    Pipeline de compression en 2 passes :
    - Passe 1 : Extraction exhaustive (perte <30%)
    - Passe 2 : Compression sélective (perte supplémentaire <30%)
    - Total : Perte cible <60% (vs 90% actuellement)
    """

    def __init__(self, llm_client, validation_func):
        self.llm_client = llm_client
        self.validation_func = validation_func

    def pass1_exhaustive_extraction(self, document_text: str) -> Dict:
        """
        PASSE 1 : Extraction exhaustive sans perte d'information.

        Objectif : Extraire TOUT, même si le JSON est volumineux.
        Format : Verbeux avec redondance autorisée.
        Contrainte : Tolérance à la taille (JSON de 100KB autorisé).
        """

        # Mapper la structure d'abord
        structure = map_document_structure(document_text)

        system_prompt = """
Vous êtes un assistant juridique expert en extraction structurée.

OBJECTIF DE CETTE PASSE : EXTRACTION EXHAUSTIVE SANS PERTE D'INFORMATION

CONSIGNES :
1. Extraire TOUS les griefs/moyens/arguments (ne rien omettre)
2. Reproduire TOUS les montants avec leur libellé exact
3. Conserver TOUTES les citations verbatim importantes
4. Répéter les informations si nécessaire (redondance autorisée)
5. NE PAS condenser ni résumer à cette étape

FORMAT JSON VERBEUX AUTORISÉ :
- Taille cible : Pas de limite stricte (100KB acceptable)
- Privilégier la complétude sur la concision
- Dupliquer les participants dans chaque section si besoin

EXEMPLE :
Si un grief fait 500 lignes dans l'original, votre extraction peut faire 300 lignes
(ratio 60%, acceptable pour cette passe).
"""

        user_prompt = f"""
{structure['auto_check_instructions']}

Extraire le document suivant en JSON structuré EXHAUSTIF.

DOCUMENT :
{document_text}
"""

        response = self.llm_client.chat.completions.create(
            model="claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=32000,  # Autoriser des réponses longues
            temperature=0.0
        )

        json_pass1 = json.loads(response.choices[0].message.content)

        return {
            'json': json_pass1,
            'size_kb': len(json.dumps(json_pass1)) / 1024,
            'pass': 1
        }

    def pass2_selective_compression(self, json_pass1: Dict) -> Dict:
        """
        PASSE 2 : Compression sélective en gardant l'essentiel.

        Objectif : Réduire la taille tout en gardant les informations critiques.
        Format : JSON optimisé.
        Contrainte : Taille cible 50KB, perte max 50% vs passe 1.
        """

        system_prompt = """
Vous êtes un assistant juridique expert en compression de données structurées.

OBJECTIF DE CETTE PASSE : COMPRESSION SÉLECTIVE EN GARDANT L'ESSENTIEL

CONSIGNES :
1. CONSERVER INTÉGRALEMENT :
   - Tous les griefs (ne pas fusionner)
   - Tous les montants chiffrés
   - Toutes les références légales
   - La hiérarchie principal/subsidiaire
   - 1-2 verbatim clés par grief

2. COMPRESSER RAISONNABLEMENT :
   - Fusionner arguments redondants (ex: 5 arguments similaires → 2 arguments synthétiques)
   - Déduplicater les participants identiques entre sections
   - Raccourcir les key_source_excerpt (200 mots → 100 mots)
   - Simplifier les thesis trop verbeux

3. NE JAMAIS :
   - Supprimer des griefs
   - Agréger des montants en "etc."
   - Perdre la hiérarchie des sections

TAILLE CIBLE : 50KB (vs ~100KB en passe 1)
PERTE ACCEPTABLE : 50% du volume, mais 0% des informations critiques
"""

        user_prompt = f"""
Compresser le JSON suivant en appliquant les règles de compression sélective.

JSON À COMPRESSER (PASSE 1) :
{json.dumps(json_pass1, ensure_ascii=False, indent=2)}
"""

        response = self.llm_client.chat.completions.create(
            model="claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=16000,
            temperature=0.0
        )

        json_pass2 = json.loads(response.choices[0].message.content)

        return {
            'json': json_pass2,
            'size_kb': len(json.dumps(json_pass2)) / 1024,
            'pass': 2
        }

    def run(self, document_text: str, original_text_for_validation: str) -> Optional[Dict]:
        """
        Exécuter le pipeline en 2 passes avec validation à chaque étape.
        """

        print("=" * 80)
        print("PIPELINE DE COMPRESSION EN 2 PASSES")
        print("=" * 80)

        # ===================================================================
        # PASSE 1 : EXTRACTION EXHAUSTIVE
        # ===================================================================

        print("\n🔵 PASSE 1 : Extraction exhaustive...")
        result_pass1 = self.pass1_exhaustive_extraction(document_text)

        print(f"   Taille JSON passe 1 : {result_pass1['size_kb']:.2f} KB")

        # Validation passe 1
        print("   Validation passe 1...")
        validation_pass1 = self.validation_func(
            original_text_for_validation,
            "",  # Pas de texte intimé pour l'instant
            [result_pass1['json']]  # Format liste de packets
        )

        if not validation_pass1.valid:
            print("   ❌ PASSE 1 INVALIDE - ERREURS CRITIQUES :")
            for error in validation_pass1.errors:
                print(f"      - {error['message']}")
            print("   → ARRÊT DU PIPELINE, CORRECTION NÉCESSAIRE")
            return None

        print(f"   ✅ Passe 1 valide (score complétude : {validation_pass1.metrics['global_completeness_score']:.1%})")

        # ===================================================================
        # PASSE 2 : COMPRESSION SÉLECTIVE
        # ===================================================================

        print("\n🟢 PASSE 2 : Compression sélective...")
        result_pass2 = self.pass2_selective_compression(result_pass1['json'])

        print(f"   Taille JSON passe 2 : {result_pass2['size_kb']:.2f} KB")
        print(f"   Réduction : {result_pass1['size_kb']:.2f} KB → {result_pass2['size_kb']:.2f} KB ({(1 - result_pass2['size_kb']/result_pass1['size_kb'])*100:.1f}% de compression)")

        # Validation passe 2
        print("   Validation passe 2...")
        validation_pass2 = self.validation_func(
            original_text_for_validation,
            "",
            [result_pass2['json']]
        )

        if not validation_pass2.valid:
            print("   ❌ PASSE 2 INVALIDE - ERREURS CRITIQUES :")
            for error in validation_pass2.errors:
                print(f"      - {error['message']}")
            print("   → REVENIR À LA PASSE 1 (JSON exhaustif)")
            return result_pass1

        print(f"   ✅ Passe 2 valide (score complétude : {validation_pass2.metrics['global_completeness_score']:.1%})")

        # ===================================================================
        # COMPARAISON ET DÉCISION
        # ===================================================================

        print("\n📊 COMPARAISON DES 2 PASSES :")
        print(f"   Taille passe 1 : {result_pass1['size_kb']:.2f} KB | Score : {validation_pass1.metrics['global_completeness_score']:.1%}")
        print(f"   Taille passe 2 : {result_pass2['size_kb']:.2f} KB | Score : {validation_pass2.metrics['global_completeness_score']:.1%}")

        score_loss = validation_pass1.metrics['global_completeness_score'] - validation_pass2.metrics['global_completeness_score']

        if score_loss > 0.10:  # >10% de perte de complétude
            print(f"   ⚠️  Perte de complétude trop importante ({score_loss:.1%})")
            print("   → UTILISER PASSE 1 (exhaustif) plutôt que passe 2")
            return result_pass1
        else:
            print(f"   ✅ Perte de complétude acceptable ({score_loss:.1%})")
            print("   → UTILISER PASSE 2 (compressé)")
            return result_pass2

# ===================================================================
# UTILISATION
# ===================================================================

if __name__ == "__main__":
    # Charger les documents
    with open('/path/to/Dossier_6_conclusion_appelant.txt', 'r', encoding='utf-8') as f:
        doc_appelant = f.read()

    # Simuler un client LLM
    class MockLLMClient:
        pass

    llm_client = MockLLMClient()

    # Créer le pipeline
    pipeline = TwoPassCompressionPipeline(
        llm_client=llm_client,
        validation_func=validate_compression  # Définie plus haut
    )

    # Exécuter
    result = pipeline.run(
        document_text=doc_appelant,
        original_text_for_validation=doc_appelant
    )

    if result:
        # Sauvegarder le meilleur résultat
        output_file = f"dossier_6_compresse_pass{result['pass']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result['json'], f, ensure_ascii=False, indent=2)

        print(f"\n✅ Pipeline terminé avec succès")
        print(f"   Fichier sauvegardé : {output_file}")
        print(f"   Taille finale : {result['size_kb']:.2f} KB")
        print(f"   Passe utilisée : {result['pass']}")
```

---

## 6. CONCLUSION ET NEXT STEPS

Ces exemples de code permettent d'implémenter les 3 actions prioritaires identifiées :

1. **Prompt griefs numérotés** → Section 1
2. **Validation automatique** → Section 2
3. **Hiérarchie principal/subsidiaire** → Section 3

**Next steps recommandés :**

1. Intégrer ces fonctions dans le pipeline de compression existant
2. Tester sur le dossier 6 avec les corrections
3. Valider que le score global passe de 45% à 75%+
4. Appliquer aux autres dossiers

**Temps estimé d'intégration :** 1 journée de développement + 0.5 journée de tests.
