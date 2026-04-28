# Module de Compression Simplifiée

## Vue d'ensemble

Ce module implémente un pipeline de compression "intelligent" qui réduit sélectivement les parties narratives d'une conclusion juridique tout en préservant intégralement les sections juridiques critiques.

## Architecture

```
compression_simple/
├── __init__.py                    # Point d'entrée du module
├── orchestrator.py                # 🎯 Fonction principale du pipeline
├── structure_identification.py   # Étape 1: Identification de la structure
├── subsection_reduction.py       # Étape 2: Réduction des sous-sections
├── document_reconstruction.py    # Étape 3: Reconstitution du document
└── utils.py                       # Fonctions utilitaires
```

## Pipeline (4 étapes)

### Étape 1: Identification de la structure
**Module:** `structure_identification.py`
**Méthode:** 🚀 **Regex patterns** (pas d'appel API !)
**Avantages:** Instantané, gratuit, déterministe

Analyse le document par patterns regex et extrait sa structure en 4 sections principales:
- **FAITS** → Découpage en sous-sections
- **PROCÉDURE** → Découpage en sous-sections
- **MOYENS** → Contenu intégral (pas de découpage)
- **PRÉTENTIONS** → Contenu intégral (pas de découpage)

### Étape 2: Réduction ciblée
**Module:** `subsection_reduction.py`
**Prompt:** `prompts/resume_subsection.md`
**Modèle:** Mistral Large

Réduit de 20% les sous-sections de FAITS et PROCÉDURE qui dépassent 7000 tokens.
Les sections MOYENS et PRÉTENTIONS restent **intactes**.

**Ce qui est conservé:**
- ✅ Dates précises
- ✅ Noms de personnes
- ✅ Montants financiers
- ✅ Événements factuels
- ✅ Références aux pièces
- ✅ Chronologie exacte

**Ce qui est réduit:**
- ❌ Répétitions
- ❌ Formulations verbeuses
- ❌ Développements de contexte général

### Étape 3: Reconstitution
**Module:** `document_reconstruction.py`

Reconstruit un document Markdown complet avec:
- Sous-sections réduites de Faits/Procédure
- Contenu original intégral de Moyens/Prétentions

### Étape 4: Résumé final
**Module:** `orchestrator.py`
**Prompt:** `prompts/resume_conclusions.md` (ou autre)
**Modèle:** Au choix (Mistral Large, etc.)

Génère le résumé structuré final (5 pages max).

## Utilisation

```python
from compression_simple import run_simple_compression_pipeline

final_summary, intermediary_data = run_simple_compression_pipeline(
    document="[texte de la conclusion]",
    api_key="mistral_api_key",
    final_model="mistral-large-latest",
    final_prompt="resume_conclusions",
    threshold_tokens=7000,        # Seuil pour réduction
    reduction_pct=20.0,            # Taux de réduction
    progress_callback=None         # Fonction pour afficher la progression
)
```

## Données retournées

```python
intermediary_data = {
    "structure_initiale": dict,           # Structure identifiée
    "sous_sections_reduites": list,       # Liste des sous-sections réduites
    "document_reconstitue": str,          # Document reconstitué
    "tokens_original": int,               # Tokens du document original
    "tokens_reconstitue": int,            # Tokens après reconstitution
    "tokens_final": int                   # Tokens du résumé final
}
```

## Avantages

- ⚡ **Rapide**: 3-5 appels API (vs des dizaines pour compression standard)
- 🎯 **Intelligent**: Ne touche pas aux arguments juridiques
- 🔍 **Préservation**: Conserve tous les éléments factuels clés
- 📊 **Traçabilité**: Document reconstitué disponible pour vérification
