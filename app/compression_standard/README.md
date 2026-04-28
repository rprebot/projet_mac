# Module de Compression Standard (par paquets)

## Vue d'ensemble

Ce module implémente un pipeline de compression par découpage en paquets et extraction JSON structurée. Adapté aux documents très longs (> 150k tokens).

## Architecture

```
compression_standard/
├── __init__.py           # Point d'entrée du module
├── orchestrator.py       # 🎯 Fonction principale du pipeline
├── models.py             # Classes SectionNode et Packet
├── constants.py          # Patterns regex et constantes
└── utils.py              # Fonctions utilitaires
```

**Note:** Ce module réutilise temporairement le code de `document_compression.py` (déplacé dans `old/`). Un refactoring complet est prévu pour extraire toute la logique dans des modules séparés.

## Pipeline (4 étapes)

### Étape 1: Parsing
**Module:** `document_compression.py` (via orchestrator)

Parse le document en sections logiques (SectionNode) en détectant:
- Titres et sous-titres (niveaux hiérarchiques)
- Types de sections (faits, procédure, moyens, prétentions)
- Métadonnées (articles, jurisprudence, dates, montants, entités)

### Étape 2: Packetisation
**Module:** `document_compression.py` (via orchestrator)

Découpe les sections en paquets respectant un budget de tokens:
- Budget max: 42 000 tokens par paquet
- Réserve: 2500 tokens (prompt) + 3000 tokens (output)
- Budget contenu: ~36 500 tokens

### Étape 3: Extraction JSON (parallèle)
**Module:** `orchestrator.py`
**Prompt système:** Généré dynamiquement
**Modèle:** Mistral Small (rapide)

Pour chaque paquet (en parallèle avec 2 workers):
- Extrait un JSON structuré avec sections, arguments, références légales
- Identifie les participants et leur rôle
- Conserve extraits sources et points verbatim

### Étape 4: Synthèse finale
**Module:** `orchestrator.py`
**Prompt:** `prompts/resume_conclusions_compression_mode.md` ou `synthese_faits_procedure_moyens_compression_mode.md`
**Modèle:** Au choix

Génère le résumé final à partir des JSON intermédiaires.

## Utilisation

```python
from compression_standard import run_standard_compression_pipeline

result = run_standard_compression_pipeline(
    document="[texte de la conclusion]",
    model_choice="Mistral Large 2",
    prompt_type="resume_conclusions",  # ou "rapport_synthese"
    progress_callback=None,
    call_model_fn=call_model,
    call_extraction_fn=call_model_fast_extraction
)
```

## Données retournées

```python
result = {
    "nb_sections": int,                  # Nombre de sections détectées
    "nb_packets": int,                   # Nombre de paquets créés
    "extracted_jsons": list,             # JSON intermédiaires
    "final_system_prompt": str,          # Prompt système utilisé
    "final_user_prompt": str,            # Prompt user utilisé
    "final_response": str,               # Résumé final
    "tokens_original": int,              # Tokens du document original
    "tokens_compressed": int,            # Tokens après compression
    "compression_ratio": float           # Ratio de compression (%)
}
```

## Avantages vs Compression Simplifiée

| Critère | Standard | Simplifiée |
|---------|----------|------------|
| **Cas d'usage** | Documents très longs (> 150k tokens) | Documents moyens (< 150k tokens) |
| **Granularité** | Paquets de ~42k tokens | Sous-sections |
| **Parallélisation** | Oui (2 workers) | Non |
| **Nb appels API** | 2 × nb_paquets + 1 | 3-5 |
| **Compression** | Tout est compressé | Faits/Procédure seulement |

## TODO - Refactoring

- [ ] Extraire le parsing dans `parsing.py`
- [ ] Extraire la packetisation dans `packetization.py`
- [ ] Extraire les fonctions d'entités dans `entities.py`
- [ ] Extraire les builders de prompts dans `prompts.py`
- [ ] Supprimer la dépendance à `document_compression.py`
