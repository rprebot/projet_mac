# Architecture de l'Application

## Structure des Dossiers

```
POC_MAC/
├── app.py                        # 🚀 Lanceur (point d'entrée)
├── requirements.txt
├── .env                          # Configuration (clés API)
│
├── app/                          # 📁 Application principale
│   ├── app.py                    # Interface Streamlit
│   │
│   ├── compression_simple/       # 🎯 Mode compression simplifiée
│   │   ├── __init__.py
│   │   ├── README.md
│   │   ├── orchestrator.py       # ⭐ Fonction principale du pipeline
│   │   ├── structure_identification.py
│   │   ├── subsection_reduction.py
│   │   ├── document_reconstruction.py
│   │   └── utils.py
│   │
│   ├── compression_standard/     # 📦 Mode compression par paquets
│   │   ├── __init__.py
│   │   ├── README.md
│   │   ├── orchestrator.py       # ⭐ Fonction principale du pipeline
│   │   ├── models.py
│   │   ├── constants.py
│   │   └── utils.py
│   │
│   ├── prompts/                  # 📝 Prompts système
│   │   ├── identification_structure.md
│   │   ├── resume_subsection.md
│   │   ├── resume_conclusions.md
│   │   ├── resume_conclusions_compression_mode.md
│   │   ├── synthese_faits_procedure_moyens.md
│   │   └── synthese_faits_procedure_moyens_compression_mode.md
│   │
│   └── dossiers/                 # 📄 Fichiers de test (conclusions)
│       └── Dossier_*.txt
│
├── analyse/                      # 📊 Scripts d'analyse et rapports
│   ├── data/
│   ├── output/
│   └── scripts/
│       └── analyse_notations.py
│
└── old/                          # 🗄️ Fichiers archivés
    ├── MEMO TEST LLM.docx
    ├── long_text_summary.ipynb
    ├── dossier_6_compresse.json
    ├── simple_compression.py      # ⚠️ Remplacé par compression_simple/
    └── document_compression.py    # ⚠️ Remplacé par compression_standard/
```

## Modes de Compression

### 🎯 Mode Compression Simplifiée

**Fichiers:** `app/compression_simple/`

**Pipeline:**
1. Identification de la structure (Faits, Procédure, Moyens, Prétentions)
2. Réduction ciblée des sous-sections volumineuses (Faits/Procédure > 7000 tokens)
3. Reconstitution du document
4. Résumé final

**Point d'entrée:**
```python
from compression_simple import run_simple_compression_pipeline
```

**Avantages:**
- ⚡ Rapide (3-5 appels API)
- 🎯 Préserve intégralement les Moyens et Prétentions
- 🔍 Conservation des éléments factuels clés

**Cas d'usage:** Documents moyens (< 150k tokens)

---

### 📦 Mode Compression Standard (par paquets)

**Fichiers:** `app/compression_standard/`

**Pipeline:**
1. Parsing du document en sections
2. Packetisation (découpage en paquets de ~42k tokens)
3. Extraction JSON pour chaque paquet (en parallèle)
4. Synthèse finale à partir des JSON

**Point d'entrée:**
```python
from compression_standard import run_standard_compression_pipeline
```

**Avantages:**
- 📦 Traite les documents très longs
- ⚡ Parallélisation (2 workers)
- 📊 Compression agressive

**Cas d'usage:** Documents très longs (> 150k tokens)

---

## Changements Effectués

### ✅ Réorganisation

1. **Compression simplifiée** : Code extrait de `simple_compression.py` → modules dans `compression_simple/`
2. **Compression standard** : Code de `document_compression.py` → orchestrateur dans `compression_standard/`
3. **app.py** : Imports mis à jour pour utiliser les nouveaux modules
4. **Anciens fichiers** : Déplacés dans `old/` pour référence

### 📝 Documentation

- Chaque module a un README expliquant son fonctionnement
- Ce fichier ARCHITECTURE.md documente la structure globale

### 🎯 Points d'Entrée Simplifiés

**Avant:**
```python
from simple_compression import simple_compression_pipeline
from document_compression import parse_and_packetize, build_extraction_system_prompt, ...
```

**Après:**
```python
from compression_simple import run_simple_compression_pipeline
from compression_standard import run_standard_compression_pipeline
```

---

## Prochaines Étapes (TODO)

### Refactoring compression_standard

Actuellement, `compression_standard/orchestrator.py` importe encore `document_compression.py` (dans `old/`).

**À faire:**
- [ ] Extraire le code de parsing dans `compression_standard/parsing.py`
- [ ] Extraire la packetisation dans `compression_standard/packetization.py`
- [ ] Extraire les entités dans `compression_standard/entities.py`
- [ ] Extraire les prompts builders dans `compression_standard/prompts.py`
- [ ] Supprimer la dépendance à `document_compression.py`

### Tests

- [ ] Tester que l'application fonctionne avec les nouveaux imports
- [ ] Vérifier que les deux modes de compression fonctionnent correctement
- [ ] Tester sur différents dossiers

---

## Utilisation

### Lancer l'application

```bash
streamlit run app.py
```

### Tester en ligne de commande

```python
# Test compression simplifiée
from app.compression_simple import run_simple_compression_pipeline
import os

api_key = os.getenv("MISTRAL_API_KEY")
with open("app/dossiers/Dossier_4_conclusion_appelante.txt") as f:
    document = f.read()

summary, data = run_simple_compression_pipeline(
    document=document,
    api_key=api_key
)
print(summary)
```
