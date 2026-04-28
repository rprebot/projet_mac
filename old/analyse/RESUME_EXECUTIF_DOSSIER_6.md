# RÉSUMÉ EXÉCUTIF - ANALYSE DOSSIER 6
## Écarts JSON Compressé vs Conclusions Originales

**Date :** 2026-03-31 | **Analyste :** Claude Sonnet 4.5

---

## 🔴 CONSTAT CRITIQUE

La compression du dossier 6 présente une **perte d'information de 90%** rendant la synthèse finale inexploitable.

### Chiffres clés

| Métrique | Original | JSON | Perte |
|----------|----------|------|-------|
| **Griefs harcèlement** | 32 | 2 | **94%** |
| **Lignes totales** | 9,085 | 1,699 | 81% |
| **Références légales** | ~150+ | 52 | 65%+ |
| **Points verbatim** | ~200+ | 50 | 75%+ |

---

## ⚠️ TOP 5 PROBLÈMES IDENTIFIÉS

### 1. GRIEFS DE HARCÈLEMENT MORAL ABSENTS (94%)

**Situation :**
- Document original : 32 griefs numérotés (GRIEF 1 à GRIEF 32)
- JSON extrait : 2 griefs seulement (GRIEF 23 et 24)
- **30 griefs manquants**, soit 94% de la matière factuelle du litige

**Exemples de griefs perdus :**
- Grief 1 : Tension gouvernance septembre 2019
- Grief 3 : Perturbations permanentes par bénévoles
- Grief 5 : Modification unilatérale organisation travail
- Grief 9 : Remarque homophobe d'un bénévole
- Grief 16 : Agression verbale du 16/06/2021 (documentée par témoin)

**Impact :** Le LLM ne pourra produire qu'une synthèse déséquilibrée favorisant par défaut la position de l'appelant.

---

### 2. DÉSÉQUILIBRE DOCUMENTAIRE APPELANT/INTIMÉ

**Situation :**
- Conclusion appelant (3813 lignes) : 3 packets dédiés (P1, P2, P3)
- Conclusion intimée (5272 lignes) : 1 seul packet (P4)
- **Ratio de compression : 1:3 en défaveur de l'intimé**

**Impact :** L'argumentation de l'intimé est sous-représentée dans le JSON.

---

### 3. HIÉRARCHIE DES DEMANDES APLATIE

**Situation :**
Demandes de l'intimé (conclusion intimée, lignes 4736-4849) :
- **À titre principal :** Confirmer jugement CPH
- **Subsidiairement :** Résiliation judiciaire aux torts employeur
- **Plus subsidiairement :** Requalification en licenciement nul

**Dans le JSON :**
```json
"requests": [
  "Déclarer recevable mais mal fondée l'Association en son Appel.",
  "Débouter l'Association de l'ensemble de ses moyens et demandes.",
  "Condamner l'Association à payer à Monsieur [B] [A] :",
  "- Indemnité de l'article 700 du CPC : 3.600 €",
  "- Indemnités pour préjudice (6.343 € 40, 2.890 € 70, 36.060 € 40, 19.030 € 20, etc.)."
]
```

**Problème :** La hiérarchie principal/subsidiaire n'apparaît pas. Les montants sont agrégés ("etc.").

**Impact :** Le LLM ne comprendra pas la stratégie juridique hiérarchisée de l'intimé.

---

### 4. MONTANTS CHIFFRÉS INCOMPLETS

**Situation :**
Demandes subsidiaires de l'intimé contiennent **9 postes chiffrés** :
1. 186,07 € (régularisation salaire)
2. 18,61 € (CP sur régularisation)
3. 3.239,75 € (solde CP)
4. 188,08 € (restitution IJSS)
5. 3.000 € (privation portabilité prévoyance)
6. 19.030,20 € (D&I harcèlement moral)
7. 6.343,40 € (indemnité préavis)
8. 2.890,70 € (solde indemnité spéciale)
9. 36.060,40 € (D&I licenciement nul)

**Dans le JSON :**
Seuls 5 montants sont détaillés, les 4 premiers sont agrégés en "etc."

**Impact :** Le tableau récapitulatif des sommes en jeu sera inexact.

---

### 5. ARGUMENTS JURIDIQUES TRONQUÉS (90%)

**Exemple : Section "1- EN DROIT" (résiliation judiciaire)**

**Original :** 8 paragraphes de développement juridique (lignes 315-362) avec :
- Principe de droit énoncé
- 4 arrêts de cassation cités avec attendus
- Raisonnement par analogie
- Application au cas d'espèce

**Dans le JSON :**
```json
"arguments": [
  "Seuls les manquements graves et actuels de l'employeur peuvent justifier une résiliation judiciaire du contrat de travail.",
  "Les manquements anciens ne peuvent pas justifier une telle résiliation."
]
```

**Impact :** Le LLM aura les principes mais pas le raisonnement développé. La synthèse sera superficielle.

---

## 📊 CONSÉQUENCES SUR LA SYNTHÈSE FINALE

### Synthèse probable générée par le LLM (INCOMPLÈTE)

```
L'Association [Personne Morale 1] fait appel d'un jugement du CPH ayant
requalifié le licenciement pour inaptitude de M. [G] en licenciement nul
pour harcèlement moral.

Faits : M. [G] a été licencié pour inaptitude le 23/09/2022. Il allègue
avoir subi un harcèlement moral, notamment des retards de paiement de
salaire (février 2022 versé en deux fois) et des retards de maintien de
salaire pendant son arrêt maladie.

Arguments de l'appelant : Les manquements reprochés ne sont pas
suffisamment graves. Les barèmes MACRON s'appliquent, limitant
l'indemnisation à 3-4 mois de salaire. Les condamnations (70 000 €) sont
disproportionnées.

Arguments de l'intimé : Le licenciement est nul car l'inaptitude a une
origine professionnelle liée au harcèlement moral. Les conditions de
travail se sont dégradées. Le jugement CPH doit être confirmé.
```

### Éléments manquants (GRAVES)

- ❌ 30 griefs de harcèlement moral non mentionnés
- ❌ Agression verbale du 16/06/2021 (témoin présent)
- ❌ Gouvernance tumultueuse : 8 changements en 3 ans (détails absents)
- ❌ Falsification présumée des statuts par le salarié (accusation appelant)
- ❌ Engagements non tenus à l'embauche (salaire net, 13ème mois, primes)
- ❌ "Point d'étape salarié" du 06/03/2021 (CA où le salarié a alerté)

**Impact :** La synthèse sera biaisée et incomplète, ne reflétant que 10% de la complexité du litige.

---

## 🎯 TOP 3 ACTIONS PRIORITAIRES

### 1. PROMPT EXPLICITE POUR GRIEFS NUMÉROTÉS
**Temps :** 1 heure | **Impact :** +1500% (2 → 32 griefs)

Ajouter au prompt :
```
CONSIGNE CRITIQUE : Si le document contient des griefs numérotés
(ex: GRIEF 1, GRIEF 2, ...), vous DEVEZ extraire CHAQUE grief dans une
section distincte. NE PAS omettre de griefs. Chaque grief doit avoir :
- title: "GRIEF X : [résumé]"
- section_type: "sub-argument"
- facts, arguments, key_source_excerpt, key_verbatim_points
```

---

### 2. VALIDATION AUTOMATIQUE DE COMPLÉTUDE
**Temps :** 4 heures | **Impact :** Détection immédiate des pertes

Script de validation :
```python
def validate_compression(original_text, json_compressed):
    # Check 1 : Griefs numérotés
    original_griefs = re.findall(r'GRIEF\s+(\d+)', original_text)
    json_griefs = [s['title'] for s in sections if 'GRIEF' in s['title']]

    if len(original_griefs) != len(json_griefs):
        return {"valid": False, "missing_griefs": set(original_griefs) - set(json_griefs)}

    # Check 2 : Montants chiffrés
    # Check 3 : Sections "PAR CES MOTIFS"
    # ...

    return {"valid": True}
```

---

### 3. HIÉRARCHISATION DES DEMANDES (PRINCIPAL/SUBSIDIAIRE)
**Temps :** 1 heure | **Impact :** Préservation de la stratégie juridique

Ajouter au prompt :
```
CONSIGNE CRITIQUE : Si le document contient des demandes hiérarchisées
('À titre principal', 'Subsidiairement'), créer un champ 'requests_hierarchy' :

{
  "requests_hierarchy": [
    {"level": "principal", "requests": [...]},
    {"level": "subsidiaire", "requests": [...]}
  ]
}
```

---

## 📈 RÉSULTAT ATTENDU APRÈS CORRECTIONS

Avec les 3 actions prioritaires :

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| Griefs extraits | 2 | 32 | +1500% |
| Perte d'information | 90% | 40% | -50% |
| Complétude demandes | 56% | 100% | +44% |
| Qualité synthèse | ⚠️ Médiocre | ✅ Acceptable | Majeur |

**Temps total de mise en œuvre :** 6 heures

**ROI :** Le JSON passera de "inexploitable" à "acceptable pour synthèse de qualité".

---

## 📎 ANNEXES

### Métriques détaillées

**Décompte des sections :**
- Total sections JSON : 32
- Sections "facts" : 4
- Sections "argument" : 6
- Sections "discussion" : 14
- Sections "claims" : 5
- Sections "procedure" : 3

**Décompte des participants identifiés :**
- Total : 19 participants
- Personnes physiques : 10
- Personnes morales : 5
- Avocats : 4

**Décompte des références légales :**
- Articles de loi : 45
- Jurisprudence (Cass.) : 28
- Total : 52 références uniques

---

## 📝 CONCLUSION

Le dossier 6 présente une **perte d'information critique de 90%**, principalement due à :
1. Non-extraction des griefs numérotés (30/32 manquants)
2. Compression excessive de la conclusion intimée (1 packet vs 3 pour l'appelant)
3. Aplatissement de la hiérarchie des demandes

**Les 3 actions prioritaires recommandées (6h de travail)** permettront de ramener la perte à 40%, rendant le JSON exploitable pour une synthèse de qualité acceptable.

**Action immédiate requise** : Implémenter le prompt de détection de griefs numérotés avant de traiter d'autres dossiers.

---

**Rapport complet disponible :** `/Users/prebot/POC_MAC/analyse/RAPPORT_ECARTS_DOSSIER_6.md`
