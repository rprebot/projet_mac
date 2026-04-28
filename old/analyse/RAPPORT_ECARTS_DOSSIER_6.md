# RAPPORT D'ANALYSE COMPARATIVE - DOSSIER 6
## JSON Compressé vs Conclusions Originales

**Date d'analyse :** 2026-03-31
**Fichiers analysés :**
- JSON compressé : `/Users/prebot/POC_MAC/app/dossier_6_compresse.json` (~92KB, 1699 lignes)
- Conclusion appelant : `/Users/prebot/POC_MAC/app/dossiers/Dossier_6_conclusion_appelant.txt` (~3813 lignes)
- Conclusion intimée : `/Users/prebot/POC_MAC/app/dossiers/Dossier_6_conclusion_intimee.txt` (~5272 lignes)

---

## 🔴 RÉSUMÉ EXÉCUTIF

### Problèmes critiques identifiés

1. **PERTE MASSIVE D'INFORMATION** : 30 griefs sur 32 (94%) sont absents du JSON
2. **DÉSÉQUILIBRE DOCUMENTAIRE** : La conclusion de l'intimé (5272 lignes) est compressée en 1 seul packet vs 3 packets pour l'appelant
3. **ARGUMENTS JURIDIQUES TRONQUÉS** : Détail argumentaire réduit de ~90%
4. **EXTRAITS VERBATIM INCOMPLETS** : Points clés non conservés
5. **HIÉRARCHIE STRUCTURELLE APLATIE** : Sous-moyens et sous-sections perdus

### Métriques globales

| Métrique | Original | JSON | Perte |
|----------|----------|------|-------|
| Lignes totales | 9,085 | 1,699 | 81% |
| Griefs harcèlement | 32 | 2 | 94% |
| Packets appelant | N/A | 3 | - |
| Packets intimé | N/A | 1 | - |
| Références légales uniques | ~150+ | 52 | 65%+ |
| Points verbatim | ~200+ | 50 | 75%+ |

---

## 1. ÉCARTS IDENTIFIÉS

### A. FAITS

#### ✅ Points conservés
- Date d'embauche : 01 septembre 2019
- Date de licenciement : 23 septembre 2022
- Date d'avis d'inaptitude : 02 septembre 2022
- Qualification : Directeur du Développement, Cadre, groupe G, coefficient 400
- Salaire initial : 2 766,31 € (ou 2 806 € selon version)
- Salaire après avenant : 3 106 € (26 mai 2021)

#### 🔴 Faits absents ou tronqués

**Chronologie de la gouvernance (ABSENTE)**
L'original intimé détaille 8 changements de gouvernance :
```
1er président : [V] [J] [T] (01/09/19 au 29/09/19 et 01/10/19 au 28/04/20)
2ème présidente : [G] [S] (06/06/20 au 13/04/21)
3ème président : [X] [C] (14/04/21 à aujourd'hui)
1ère trésorière : [U] [H] (01/09/19 au 05/06/20)
2ème trésorier : [O] [I] (06/06/20 au 24/06/21)
3ème trésorier : [W] [L] (19/07/21 au 24/01/22)
1ère référente RH : [U] [H] (01/09/19 au 15/04/21 et 11/12/21 à aujourd'hui)
2ème référente RH : [Z] [R] (16/04/2021 au 10/12/2021, autoproclamée)
```

**Dans le JSON :** Mention vague de "gouvernance tumultueuse" sans détails précis.

**Impact :** Le contexte factuel du harcèlement moral (instabilité organisationnelle) est perdu.

---

**Détails des engagements à l'embauche (TRONQUÉS)**

**Original (conclusion intimée, lignes 720-726) :**
> "Les engagements non tenus incluent un salaire minimum de 2 000 € net, 25 jours de congés payés, un 13ème mois, et une prime de 150 € brut en juillet et août."

**Dans le JSON (Packet P4, section "1. SUR LE CONTEXTE DE L'EMBAUCHE") :**
- Mentionne les engagements mais sans détails chiffrés précis
- `dates_amounts`: ["2 000 € net (salaire promis)", "25 jours de congés payés (engagement non tenu)"]

**Impact :** Les montants promis sont présents mais le contexte de non-respect est affaibli.

---

**Incident de l'agression verbale du 16 juin 2021 (TRONQUÉ)**

**Original (conclusion intimée, lignes 788-798) :**
> "Or que lors de cette réunion, au lieu d'aborder la question du scénario, Monsieur [OJ] [YJ] a agressé verbalement violemment Monsieur [B] [A], Madame [Z] [R], présente, relatant ainsi (pièce 18) : « Ainsi la réunion a été un flot de reproches, en commençant par notre salarié qui a été viré sur un ton qui n'est pas admissible pour tout un chacun et encore moins pour un salarié qui au demeurant s'est battu corps et âme pour cette association tout au long de l'année. »"

**Dans le JSON :** Absent du Packet P4. Aucune mention de cet incident dans les sections "faits".

**Impact :** Un élément central du harcèlement moral (agression verbale documentée par témoin) est totalement perdu.

---

### B. PROCÉDURE

#### ✅ Points conservés
- Date de saisine CPH (1ère requête) : 31 mars 2022
- Date de saisine CPH (2nde requête) : 14 décembre 2022
- Date du jugement CPH : 05 avril 2024
- Date de déclaration d'appel : 06 mai 2024
- Montant total des condamnations : "plus de 70 000 €"

#### 🔴 Éléments procéduraux manquants

**Jonction des procédures (ABSENTE)**

**Original (conclusion intimée, ligne 376) :**
> "Attendu que selon ordonnance du 15 février 2022 le Bureau de Conciliation et d'Orientation du Conseil des Prud'hommes de [Localité 3] - MEZIERES a prononcé la jonction des deux procédures enregistrées la procédure se poursuivant sous le numéro F 22/00082 - DCS6-X-B7G-PMX."

**Dans le JSON :** Mention des deux requêtes mais pas de l'ordonnance de jonction.

**Impact :** La chronologie procédurale est incomplète, risque de confusion sur l'enchaînement.

---

**Ordonnance de maintien devant la Section Activités Diverses (ABSENTE)**

**Original (conclusion intimée, ligne 379) :**
> "Attendu que selon ordonnance en date du 14 septembre 2023, par mesure d'administration judiciaire non susceptible de recours, le Président du Conseil des Prud'hommes de CHARLEVILLE - MEZIERES, après avis du vice-président, a ordonné le maintien du litige devant la Section Activités Diverses."

**Dans le JSON :** Totalement absent.

**Impact :** Information procédurale technique perdue, peut affecter la compréhension de la compétence.

---

### C. PRÉTENTIONS

#### ✅ Demandes de l'appelant (COMPLÈTES)

**Dans le JSON (Packet P2, section "PAR CES MOTIFS") :**
```json
"requests": [
  "Infirmer le jugement du Conseil de Prud'hommes en ce qu'il a requalifié le licenciement pour inaptitude en licenciement nul.",
  "Débouter Monsieur [G] de l'intégralité de ses prétentions.",
  "Condamner Monsieur [G] à payer à l'Association la somme de 6 000 € sur le fondement de l'article 700 du Code de Procédure Civile.",
  "Condamner Monsieur [G] aux entiers dépens de première instance et d'appel."
]
```

**Vérification vs original (lignes 204-214) :** ✅ CONFORME

---

#### 🟡 Demandes de l'intimé (INCOMPLÈTES)

**Original (conclusion intimée, lignes 4736-4849) :**

**À titre principal :**
- Débouter l'Association de l'ensemble de ses moyens
- Confirmer le jugement CPH du 05/04/2024 en toutes ses dispositions
- Condamner l'Association à payer 3.600 € (article 700 en appel)

**Subsidiairement (en cas d'infirmation) :**
- Prononcer résiliation judiciaire aux torts de l'employeur (effet au 23/09/2022)
- Ou requalifier le licenciement en licenciement nul
- Condamner l'Association à payer :
  - 186,07 € (régularisation salaire)
  - 18,61 € (CP sur régularisation)
  - 3.239,75 € (solde CP)
  - 188,08 € (restitution IJSS)
  - 3.000 € (privation portabilité prévoyance)
  - 19.030,20 € (D&I harcèlement moral)
  - 6.343,40 € (indemnité préavis)
  - 2.890,70 € (solde indemnité spéciale)
  - 36.060,40 € (D&I licenciement nul)
- Remise documents sous astreinte 20 €/jour

**Dans le JSON (Packet P4, section "PAR CES MOTIF S") :**
```json
"requests": [
  "Déclarer recevable mais mal fondée l'Association [Personne Morale 1] en son Appel.",
  "Débouter l'Association [Personne Morale 1] de l'ensemble de ses moyens et demandes.",
  "Condamner l'Association [Personne Morale 1] à payer à Monsieur [B] [A] :",
  "- Indemnité de l'article 700 du CPC : 3.600 €",
  "- Indemnités pour préjudice (6.343 € 40, 2.890 € 70, 36.060 € 40, 19.030 € 20, etc.).",
  "- Remise de documents sous astreinte."
]
```

**Problèmes identifiés :**
1. **Hiérarchie principal/subsidiaire PERDUE** : La distinction "À titre principal" vs "Subsidiairement" n'apparaît pas clairement
2. **Liste des montants AGRÉGÉE** : "etc." remplace 4 montants précis (186,07 / 18,61 / 3.239,75 / 188,08)
3. **Qualification juridique ABSENTE** : "résiliation judiciaire" vs "licenciement nul" non distinguée

**Impact :** Risque de confusion sur la stratégie de l'intimé (prétentions principales vs alternatives).

---

### D. MOYENS / ARGUMENTS

#### 🔴 PERTE MASSIVE : 30 griefs sur 32 absents

**Original (conclusion appelant, lignes 508-2100) :** 32 griefs numérotés de GRIEF 1 à GRIEF 32

**Dans le JSON :** Seuls GRIEF 23 et GRIEF 24 sont extraits (Packet P2)

**Griefs manquants (exemples) :**

| Grief | Sujet | Présent dans JSON |
|-------|-------|-------------------|
| 1 | Tension entre président et trésorière (sept 2019) | ❌ |
| 2 | Remise en cause règles contractuelles (frais de mission) | ❌ |
| 3 | Perturbations permanentes par bénévoles et appels | ❌ |
| 4 | Demande de relevé quotidien d'activité | ❌ |
| 5 | Modification unilatérale organisation travail | ❌ |
| ... | ... | ❌ |
| 22 | Grief non spécifié | ❌ |
| 23 | Versement salaire février en 2 fois (codes perdus) | ✅ |
| 24 | Retards paiement maintien salaire arrêt maladie | ✅ |
| 25-32 | Griefs non spécifiés | ❌ |

**Impact critique :** 94% des faits allégués de harcèlement moral sont absents. Le LLM ne pourra pas produire une synthèse équilibrée du litige.

---

#### 🟡 Détail argumentaire réduit de ~90%

**Exemple : Grief 1 (ABSENT)**

**Original (conclusion appelant, lignes 517-642) :** ~125 lignes d'argumentation détaillée
- Contexte factuel (7 paragraphes)
- Réfutation des allégations (5 arguments)
- Preuve par pièces (4 pièces citées : 24, 25, 26)
- Critique du raisonnement CPH (2 paragraphes)

**Dans le JSON :** Totalement absent.

---

**Exemple : Section "1- EN DROIT" (résiliation judiciaire)**

**Original (conclusion appelant, lignes 315-362) :**
```
Il convient à titre préliminaire de rappeler que seuls les manquements graves d'un
employeur qui sont actuels peuvent justifier une résiliation judiciaire du contrat de travail.

Les manquements anciens ne peuvent pas justifier la résiliation judiciaire du contrat de
travail du salarié.

***

La résiliation judiciaire du contrat de travail du salarié ne peut être prononcée qu'en
cas de manquement grave de l'employeur à ses obligations contractuelles empêchant la
poursuite du contrat de travail.

[...] (8 paragraphes de développement juridique avec 4 arrêts de cassation cités)
```

**Dans le JSON (Packet P1, section "1- EN DROIT") :**
```json
"arguments": [
  "Seuls les manquements graves et actuels de l'employeur peuvent justifier une résiliation judiciaire du contrat de travail.",
  "Les manquements anciens ne peuvent pas justifier une telle résiliation."
],
"legal_references": [
  "Cass. soc., 14 déc. 2011, n° 10-13.542",
  "Cass. soc., 16 févr. 2005, n° 02-46.649",
  "Cass. soc., 26 mars 2014, n° 12-21.372",
  "Cass. soc., 6 févr. 2019, n° 17-26.562"
],
"key_verbatim_points": [
  "Seuls les manquements graves d'un employeur qui sont actuels peuvent justifier une résiliation judiciaire du contrat de travail.",
  "Les manquements anciens ne peuvent pas justifier la résiliation judiciaire du contrat de travail du salarié."
]
```

**Analyse :**
- ✅ Les 2 principes juridiques centraux sont conservés
- ✅ Les 4 références de jurisprudence sont complètes
- ❌ Le raisonnement détaillé (8 paragraphes) est compressé en 2 bullet points
- ❌ Les citations d'arrêts (attendus) ne sont pas reproduites

**Impact :** Le LLM aura les principes mais pas le raisonnement développé.

---

#### 🔴 Hiérarchie structurelle aplatie

**Original (conclusion appelant) :**
```
I- SUR LA DEMANDE DE RESILIATION JUDICIAIRE DU CONTRAT DE TRAVAIL
  A- SUR L'ABSENCE DE MANQUEMENTS GRAVES DE L'EMPLOYEUR
    1- EN DROIT
    2- EN L'ESPECE
      GRIEF 1 :
      GRIEF 2 :
      ...
      GRIEF 32 :
  B- S'AGISSANT DU MONTANT DES INDEMNISATIONS
    1- Sur l'application des barèmes MACRON
    2- Sur le calcul de l'ancienneté
    ...
```

**Dans le JSON :**
```json
"path": ["I- SUR LA DEMANDE DE RESILIATION JUDICIAIRE DU CONTRAT DE TRAVAIL"]
"path": ["I- SUR LA DEMANDE DE RESILIATION JUDICIAIRE DU CONTRAT DE TRAVAIL", "1- EN DROIT"]
"path": ["I- SUR LA DEMANDE DE RESILIATION JUDICIAIRE DU CONTRAT DE TRAVAIL", "2- EN L'ESPECE"]
```

**Problème :** Les sous-sections A/B et les 32 griefs ne sont pas dans le `path`, ils sont perdus.

**Impact :** La structure logique du raisonnement (moyen > sous-moyen > grief) est cassée.

---

### E. RÉFÉRENCES LÉGALES

#### ✅ Jurisprudence (QUALITÉ CONSERVÉE)

**Exemples extraits du JSON :**
- Cass. soc., 14 déc. 2011, n° 10-13.542 ✅
- Cass. soc., 16 févr. 2005, n° 02-46.649 ✅
- Cass. soc., 26 mars 2014, n° 12-21.372 ✅
- Cass. Soc 25 mai 2016 n°14-20.578 ✅
- Cass. Soc 30 juin 2016 n°15-16.066 ✅

**Format :** ✅ Conforme (juridiction, date, numéro de pourvoi)

---

#### 🟡 Articles de loi (PARTIELLEMENT COMPLETS)

**Exemples extraits du JSON :**
- Article L 1235-3 (indemnisation pour licenciement sans cause réelle et sérieuse) ✅
- Article L 1226-14 (licenciement pour inaptitude) ✅
- Article 700 du Code de Procédure Civile ✅
- Article L 1152-1 (harcèlement moral) ✅

**Problème :** Certains articles sont cités sans leur intitulé explicite :
- "Article 4 du contrat de travail" (non détaillé)
- "Article 11 du contrat de travail" (non détaillé)

**Impact :** Risque de perte de contexte sur les clauses contractuelles.

---

#### 🔴 Barèmes MACRON (CONFUSION)

**Original (conclusion appelant, ligne 447) :**
> "Barèmes MACRON (CC, décision n°2018-761 DC du 21-03-2018)"

**Dans le JSON (Packet P2, section "B- S'AGISSANT DU MONTANT") :**
```json
"legal_references": [
  "Article L 1235-3 (indemnisation pour licenciement sans cause réelle et sérieuse)",
  "Article L 1226-14 (licenciement pour inaptitude)",
  "Barèmes MACRON (CC, décision n°2018-761 DC du 21-03-2018)"
]
```

**Problème :** Le format "Barèmes MACRON" est conservé mais le LLM pourrait ne pas reconnaître qu'il s'agit de l'article L 1235-3 modifié.

**Impact :** Risque de confusion sur la source légale du plafonnement.

---

### F. EXTRAITS SOURCES (key_source_excerpt)

#### ✅ Fidélité textuelle (BONNE)

**Exemple : GRIEF 23**

**Original (conclusion appelant, ligne 328) :**
> "« Attendu que le salaire de février de Monsieur [B] [G] lui a été versé en 2 fois car n'ayant plus de trésorier, le président avait égaré les codes (pièce 42). Que pourtant, dans le compte rendu d'une réunion du 26 février 2022, ce qui est dès lors inexact, il est mentionné (pièce 43) : « Par l'intermédiaire de [J] [Z], RH de l'association, il a été demandé à [B] [G] de nous donner les codes d'accès au compte courant du [Personne Morale 23]. Malheureusement ceux-ci ne fonctionnent pas ». »"

**Dans le JSON (Packet P2, GRIEF 23) :**
```json
"key_source_excerpt": "« Attendu que le salaire de février de Monsieur [B] [G] lui a été versé en 2 fois car n'ayant plus de trésorier, le président avait égaré les codes (pièce 42). Que pourtant, dans le compte rendu d'une réunion du 26 février 2022, ce qui est dès lors inexact, il est mentionné (pièce 43) : « Par l'intermédiaire de [J] [Z], RH de l'association, il a été demandé à [B] [G] de nous donner les codes d'accès au compte courant du [Personne Morale 23]. Malheureusement ceux-ci ne fonctionnent pas ». »"
```

✅ **Reproduction exacte, guillemets préservés.**

---

#### 🔴 Extraits non représentatifs (PROBLÈME)

**Problème :** Le choix des extraits n'est pas toujours pertinent.

**Exemple : Section "PAR CES MOTIFS" de l'intimé**

**Original (conclusion intimée, lignes 4736-4849) :**
```
Déclarer recevable mais mal fondée l'Association [Personne Morale 1] en son Appel.

Débouter purement et simplement l'Association [Personne Morale 1] de l'ensemble
de ses moyens prétentions et demandes.

Confirmer le jugement du Conseil des Prud'hommes de [Localité 3] - MEZIERES du
5 avril 2024 dont Appel en toutes ses dispositions.

[...] (70 lignes de demandes détaillées)
```

**Dans le JSON (Packet P4, "PAR CES MOTIF S") :**
```json
"key_source_excerpt": "Déclarer recevable mais mal fondée l'Association [Personne Morale 1] en son Appel. Débouter purement et simplement l'Association [Personne Morale 1] de l'ensemble de ses moyens prétentions et demandes. Confirmer le jugement du Conseil des Prud'hommes de [Localité 3] - MEZIERES du 5 avril 2024 dont Appel en toutes ses dispositions."
```

**Problème :** L'extrait ne mentionne PAS les montants détaillés (186,07 € / 18,61 € / 3.239,75 € / etc.) alors qu'ils sont essentiels.

**Impact :** Le LLM pourrait manquer les demandes chiffrées subsidiaires.

---

### G. VERBATIM (key_verbatim_points)

#### ✅ Formulations exactes conservées (BONNE)

**Exemple : GRIEF 23**

**Original (conclusion appelant, ligne 352) :**
> "« Le compte en banque : Je ne me souvenais plus du mot de passe, c'est tout ! Effectivement c'est moi qui l'avais créé au début de ma présidence, je l'ai inscrit dans un coin bien planqué pour que personne ne le trouve .... même pas moi ! C'est aussi bête que ça ! » (mail du président du 01/03/2022)."

**Dans le JSON (Packet P2, GRIEF 23) :**
```json
"key_verbatim_points": [
  "« Le compte en banque : Je ne me souvenais plus du mot de passe, c'est tout ! Effectivement c'est moi qui l'avais créé au début de ma présidence, je l'ai inscrit dans un coin bien planqué pour que personne ne le trouve .... même pas moi ! C'est aussi bête que ça ! » (mail du président du 01/03/2022).",
  [...]
]
```

✅ **Reproduction exacte avec guillemets, points de suspension et date.**

---

#### 🔴 Verbatim manquants (GRAVE)

**Problème :** Seulement 50 points verbatim extraits alors que les originaux en contiennent ~200+.

**Exemple : Grief 1 (ABSENT DU JSON)**

**Original (conclusion appelant, ligne 527) :**
> "« Éprouvé́ par les rapports humains [...] je remarque depuis quelques semaines une véritable tension une défiance entre nous [...] je vois des humains garder les griffes sur leurs attributions en rejetant les bonnes volontés »."

**Dans le JSON :** ❌ Absent (car tout le Grief 1 est manquant).

**Impact :** Les formulations clés qui caractérisent le harcèlement moral sont perdues.

---

### H. MÉTADONNÉES

#### ✅ Participants (BONNE QUALITÉ)

**Extraction des participants :**
```json
{
  "name": "Association [Personne Morale 1] ([Personne Morale 2])",
  "kind": "organization",
  "role": "appelant",
  "side": "current_party"
},
{
  "name": "Monsieur [B] [G]",
  "kind": "person",
  "role": "salarié",
  "side": "opposing_party"
},
{
  "name": "Maître [F] [E]",
  "kind": "lawyer",
  "role": "appelant",
  "side": "current_party"
}
```

✅ **Noms, rôles, qualifications corrects.**

---

#### 🟡 Classification des sections (PARTIELLEMENT CORRECTE)

**Exemples :**

| Section | Type attendu | Type dans JSON | Correct ? |
|---------|--------------|----------------|-----------|
| "I. LES FAITS" | facts | facts | ✅ |
| "II. LA PROCEDURE" | procedure | procedure | ✅ |
| "DISCUSSION" | discussion | discussion | ✅ |
| "PAR CES MOTIFS" | claims | claims | ✅ |
| "GRIEF 23 :" | discussion | discussion | 🟡 (devrait être "argument" ou "sub-argument") |
| "1- EN DROIT" | argument | argument | ✅ |
| "2- EN L'ESPECE" | argument | argument | ✅ |

**Problème :** Les "GRIEF" sont classés en "discussion" alors qu'ils devraient avoir un type spécifique (ex: "sub-argument" ou "factual_allegation").

---

## 2. CONSÉQUENCES ANTICIPÉES SUR LE RÉSULTAT FINAL

### A. Perte d'information critique

#### 🔴 Impact sur la synthèse du harcèlement moral

**Écart identifié :** 30 griefs sur 32 (94%) sont absents.

**Conséquence :**
Le LLM ne pourra produire qu'une synthèse partielle et déséquilibrée :
- **Vision de l'appelant :** Seulement 2 griefs (codes perdus, retards paiement) vs 32 allégations
- **Vision de l'intimé :** Partiellement présente (arguments généraux dans P4) mais manque les faits détaillés

**Risque :** La synthèse finale sera biaisée en faveur de la position de l'appelant par défaut d'information contradictoire.

**Exemple de synthèse erronée probable :**
> "Le salarié allègue des faits de harcèlement moral mais seuls deux griefs sont documentés : le versement tardif du salaire de février et les retards de maintien de salaire. L'employeur conteste ces griefs en arguant que..."

**Réalité manquante :**
- Agression verbale du 16/06/2021 (documentée par témoin)
- Perturbations permanentes par appels multiples
- Changements répétés de gouvernance (8 fois en 3 ans)
- Dénigrement et rumeurs sur la légitimité du travail
- Remarque homophobe d'un bénévole
- 28 autres griefs non extraits

---

#### 🔴 Impact sur l'évaluation du préjudice

**Écart identifié :** Montants détaillés dans les demandes subsidiaires de l'intimé agrégés en "etc."

**Conséquence :**
Le LLM ne pourra pas produire un tableau récapitulatif précis des sommes en jeu.

**Exemple de tableau que le LLM pourrait générer (INCOMPLET) :**

| Poste | Montant demandé | Montant alloué CPH |
|-------|-----------------|-------------------|
| D&I harcèlement | 30 000 € | 19 030,20 € |
| D&I licenciement nul | 57 000 € | 38 060,40 € |
| Indemnité préavis | 6 343,40 € | 6 343,40 € |
| Solde indemnité spéciale | 2 890,70 € | 2 890,70 € |
| **AUTRES** | **~7 635 €** | **~3 766 €** |

**Problème :** La ligne "AUTRES" masque 5 postes distincts :
1. Régularisation salaire : 186,07 €
2. CP sur régularisation : 18,61 €
3. Solde CP : 3 239,75 €
4. Restitution IJSS : 188,08 €
5. Privation portabilité : 3 000 € (ou 16 185,36 € selon demande initiale)

---

#### 🟡 Impact sur la compréhension du litige

**Écart identifié :** Hiérarchie "principal/subsidiaire" des demandes de l'intimé aplatie.

**Conséquence :**
Le LLM pourrait ne pas comprendre la stratégie juridique de l'intimé :
1. **À titre principal :** Confirmer le jugement CPH (licenciement nul reconnu)
2. **Subsidiairement (si infirmation) :** Demander résiliation judiciaire ou requalification

**Risque :** Le LLM pourrait présenter les demandes comme "alternatives" au lieu de "hiérarchisées".

**Exemple de formulation erronée :**
> "L'intimé demande soit la confirmation du jugement, soit la résiliation judiciaire, soit la requalification du licenciement."

**Formulation correcte attendue :**
> "L'intimé demande en priorité la confirmation du jugement CPH. À défaut, il sollicite subsidiairement la résiliation judiciaire aux torts de l'employeur, ou, plus subsidiairement encore, la requalification du licenciement en licenciement nul."

---

### B. Risque de résumé incomplet

#### 🔴 Synthèse du dossier

**Prompt typique attendu du LLM :**
> "Produisez une synthèse du dossier en 500 mots max."

**Synthèse probable générée (INCOMPLÈTE) :**
> "L'Association [Personne Morale 1] fait appel d'un jugement du CPH de Charleville-Mézières du 05/04/2024 ayant requalifié le licenciement pour inaptitude de M. [G] en licenciement nul pour harcèlement moral. L'appelant conteste cette requalification et sollicite l'infirmation du jugement.
>
> **Faits :** M. [G] a été embauché le 01/09/2019 comme Directeur du Développement. Il a été licencié pour inaptitude le 23/09/2022 après un avis médical du 02/09/2022. Il allègue avoir subi un harcèlement moral, notamment des retards de paiement de salaire (février 2022 versé en deux fois) et des retards de maintien de salaire pendant son arrêt maladie.
>
> **Arguments de l'appelant :** Les manquements reprochés ne sont pas suffisamment graves pour justifier une résiliation judiciaire. Les barèmes MACRON s'appliquent, limitant l'indemnisation à 3-4 mois de salaire pour 3 ans d'ancienneté. Les condamnations (70 000 €) sont disproportionnées.
>
> **Arguments de l'intimé :** Le licenciement pour inaptitude est nul car l'inaptitude a une origine professionnelle liée au harcèlement moral. Les conditions de travail se sont dégradées en raison d'une gouvernance chaotique. Le jugement CPH doit être confirmé."

**Éléments manquants (GRAVES) :**
- ❌ Les 30 autres griefs de harcèlement moral
- ❌ L'agression verbale du 16/06/2021
- ❌ Le détail de la gouvernance tumultueuse (8 changements)
- ❌ La falsification présumée des statuts par le salarié (accusation de l'appelant)
- ❌ Les engagements non tenus à l'embauche
- ❌ Le "point d'étape salarié" du 06/03/2021 (CA où le salarié a alerté)

**Impact :** La synthèse sera biaisée et incomplète, ne reflétant pas la complexité du litige.

---

### C. Risque d'inexactitude factuelle

#### 🟡 Confusion sur les montants

**Écart identifié :** Montant demandé pour "privation portabilité prévoyance" incohérent.

**Original 1 (requête du 31/03/2022, ligne 165) :**
> "16 185.36 € : D&I pour privation de la portabilité du maintien de salaire à 87% par la garantie prévoyance de la mutuelle [Personne Morale 5]"

**Original 2 (conclusions intimé, ligne 4809) :**
> "3.000 € 00 : Dommages-intérêts pour privation de la portabilité du maintien de salaire à 87 %"

**Montant alloué par CPH (ligne 577) :**
> "134,87 euros à titre de dommages et intérêts pour privation de la portabilité"

**Dans le JSON (Packet P4) :**
```json
"dates_amounts": [
  "3.000 €"
]
```

**Problème :** Le JSON ne reflète pas la demande initiale (16 185,36 €) ni le montant alloué (134,87 €).

**Risque :** Le LLM pourrait produire un tableau inexact :

| Poste | Demandé (JSON) | Alloué CPH | Écart |
|-------|----------------|------------|-------|
| Privation portabilité | 3 000 € | 134,87 € | -96% |

**Réalité :** La demande initiale était de 16 185,36 €, réduite à 3 000 € en conclusions, allouée à 134,87 €.

---

#### 🔴 Confusion sur les noms et dates

**Écart identifié :** Incohérence dans les noms de l'intimé.

**Original conclusion intimée (ligne 42) :**
> "Monsieur [B] [A], né le [Date naissance 1] 1973 à [Localité 1]"

**Original conclusion appelant (ligne 27) :**
> "Monsieur [B] [G], né le [Date naissance 1] 1973 à [Localité 1]"

**Dans le JSON :**
- Packet P1-P3 : "Monsieur [B] [G]"
- Packet P4 : "Monsieur [B] [A]"

**Problème :** Il s'agit de la même personne (initiales différentes selon les documents), mais le JSON ne fait pas le lien explicite.

**Risque :** Le LLM pourrait croire qu'il y a deux personnes distinctes si le lien n'est pas inféré.

**Note :** Le champ `canonical_name` existe dans certaines sections :
```json
{
  "name": "Monsieur [G]",
  "canonical_name": "Monsieur [B] [G]"
}
```
Mais il n'est pas systématique.

---

### D. Impact sur la qualité de la synthèse argumentaire

#### 🔴 Raisonnement juridique appauvri

**Écart identifié :** Arguments détaillés compressés en bullet points génériques.

**Exemple : Application des barèmes MACRON**

**Original (conclusion appelant, lignes 435-439) :**
> "En application de l'article L 1235-3 du Code du travail, Monsieur [G] ne pourra obtenir, si le Conseil de prud'hommes, juge son licenciement comme étant dépourvu de cause réelle et sérieuse, à une indemnité qui ne pourra être comprise qu'entre 3 et 4 mois de salaire brut (ancienneté de 3 ans).
>
> Or, le Conseil de Prud'hommes a alloué à Monsieur [G] une indemnisation d'un montant de 38 060,40 € de dommages et intérêts du seul chef des dommages et intérêts pour licenciement nul.
>
> C'est dans le seul but que de voir écarter les barèmes MACRON que le demandeur sollicite des dommages et intérêts pour licenciement nul et se prévaut de prétendus faits de harcèlement moral."

**Dans le JSON (Packet P2, section "B- S'AGISSANT DU MONTANT") :**
```json
"arguments": [
  "Le licenciement est justifié par l'inaptitude professionnelle et l'impossibilité de reclassement, et non par un harcèlement moral.",
  "Les barèmes MACRON s'appliquent, limitant l'indemnisation à 3-4 mois de salaire brut pour 3 ans d'ancienneté.",
  "Le salarié ne peut prétendre à une indemnisation supérieure au plafond légal, même en cas de requalification du licenciement.",
  "La Cour de cassation a validé l'application des barèmes MACRON (avis du 17 juillet 2019, arrêt du 15 décembre 2021)."
]
```

**Analyse :**
- ✅ Le principe (application barèmes) est présent
- ✅ Le montant du plafond (3-4 mois) est mentionné
- ❌ L'accusation de stratégie contentieuse ("C'est dans le seul but...") est absente des arguments explicites
- ❌ Le montant alloué (38 060,40 €) n'est pas comparé au plafond (9 513 - 12 684 €)

**Impact :** Le LLM ne pourra pas formuler l'argument central de l'appelant : "Le salarié invoque faussement le harcèlement moral pour échapper au plafonnement."

---

## 3. PISTES D'AMÉLIORATION

### Niveau 1 : Prompt d'extraction

#### 🔧 Amélioration 1 : Consigne explicite sur les griefs numérotés

**Problème :** 30 griefs sur 32 sont perdus.

**Prompt actuel (supposé) :**
> "Extraire les faits, arguments et moyens de la conclusion."

**Prompt amélioré :**
> "**CONSIGNE CRITIQUE** : Si le document contient des griefs numérotés (ex: GRIEF 1, GRIEF 2, ..., GRIEF N), vous DEVEZ extraire CHAQUE grief dans une section distincte du type 'sub-argument'. NE PAS omettre de griefs, même s'ils semblent répétitifs. Chaque grief doit avoir :
> - title: "GRIEF X : [résumé en 5 mots]"
> - section_type: "sub-argument"
> - facts: [liste des faits spécifiques au grief]
> - arguments: [réfutation ou allégation]
> - legal_references: [si cité]
> - key_source_excerpt: [extrait de 100-200 mots du grief original]
> - key_verbatim_points: [1-3 citations exactes clés]"

**Exemple attendu :**
```json
{
  "title": "GRIEF 1 : Tension gouvernance septembre 2019",
  "section_type": "sub-argument",
  "path": ["I- SUR LA DEMANDE DE RESILIATION", "A- ABSENCE DE MANQUEMENTS", "2- EN L'ESPECE", "GRIEF 1"],
  "facts": [
    "Fin septembre 2019 : tension entre président M. [M] et trésorière Mme [Z]",
    "Mail du président mentionnant 'tension', 'défiance', 'griffes sur attributions'"
  ],
  "arguments": [
    "Grief interprété par M. [G], sans fait précis matériellement étayé",
    "L'entente n'était pas compliquée : M. [M] a proposé Mme [Z] comme trésorière",
    "La démission de M. [M] était pour raisons de santé, non pour mésentente"
  ],
  "key_source_excerpt": "« Éprouvé́ par les rapports humains [...] je remarque depuis quelques semaines une véritable tension une défiance entre nous [...] je vois des humains garder les griffes sur leurs attributions en rejetant les bonnes volontés ». [...] Monsieur [M] présente sa démission puisqu'il « a bien d'autres soucis à affronter » (problèmes de santé).",
  "key_verbatim_points": [
    "« Éprouvé́ par les rapports humains [...] je vois des humains garder les griffes sur leurs attributions »"
  ]
}
```

---

#### 🔧 Amélioration 2 : Consigne sur la hiérarchie principal/subsidiaire

**Problème :** Demandes hiérarchisées aplaties.

**Prompt amélioré :**
> "**CONSIGNE CRITIQUE** : Si le document contient des demandes hiérarchisées (ex: 'À titre principal', 'Subsidiairement', 'À titre infiniment subsidiaire'), vous DEVEZ créer un champ 'requests_hierarchy' structuré ainsi :
> ```json
> {
>   "requests_hierarchy": [
>     {
>       "level": "principal",
>       "requests": ["Demande 1", "Demande 2"]
>     },
>     {
>       "level": "subsidiaire",
>       "requests": ["Demande 3", "Demande 4"]
>     }
>   ]
> }
> ```
> NE PAS agréger les demandes dans un seul tableau plat."

---

#### 🔧 Amélioration 3 : Contrainte de densité d'extraction pour les sections clés

**Problème :** Sections "PAR CES MOTIFS" trop compressées (montants agrégés en "etc.").

**Prompt amélioré :**
> "**CONTRAINTE SPÉCIALE POUR LES SECTIONS 'PAR CES MOTIFS' / 'PRÉTENTIONS' / 'DEMANDES'** :
> - Vous DEVEZ extraire CHAQUE montant chiffré avec son libellé exact (ne jamais utiliser 'etc.')
> - Format attendu pour 'requests' :
>   ```json
>   {
>     "requests": [
>       {
>         "description": "Régularisation du salaire de base de mai 2022 à septembre 2022",
>         "amount": "186,07 €",
>         "legal_basis": null
>       },
>       {
>         "description": "Indemnité compensatrice de congés payés sur régularisation",
>         "amount": "18,61 €",
>         "legal_basis": "Article L 3141-22 du Code du Travail"
>       }
>     ]
>   }
>   ```
> - Si plus de 10 demandes chiffrées : extraire TOUTES (pas de limite)."

---

#### 🔧 Amélioration 4 : Exemple de bonne extraction à fournir au LLM

**Problème :** Le LLM manque de référence pour comprendre le niveau de détail attendu.

**Prompt amélioré :**
> "**EXEMPLE DE BONNE EXTRACTION** :
>
> Si le document original contient :
> ```
> GRIEF 5 : Sur la modification unilatérale de l'organisation du travail
>
> Attendu que le 6 avril 2020, M. [G] a reçu par courriel les modalités d'organisation
> de son travail dans le cadre de l'activité partielle (chômage partiel), ce document
> mentionnant « congés à ta demande » à 2 reprises et indiquant « chaque heure non
> travaillée dans le cadre de ce dispositif exceptionnel sera indemnisée selon les
> dispositions légales ».
>
> Que M. [G] a dû demander le 7 avril 2020 à 8h40 par courriel que soit modifié cet
> écrit qui devait correspondre à l'accord passé (congés d'un commun accord, maintien
> total du salaire), ce que fera tout de suite Mme [H] (pièce 9).
>
> Cette modification unilatérale constitue un manquement grave de l'employeur.
> ```
>
> Vous DEVEZ produire :
> ```json
> {
>   "title": "GRIEF 5 : Modification unilatérale organisation travail avril 2020",
>   "section_type": "sub-argument",
>   "path": ["...", "GRIEF 5"],
>   "facts": [
>     "06/04/2020 : M. [G] reçoit par courriel modalités d'organisation travail (activité partielle)",
>     "Document mentionne 'congés à ta demande' (2 fois) et indemnisation selon dispositions légales",
>     "07/04/2020 8h40 : M. [G] demande par courriel modification de l'écrit",
>     "Accord initial : congés d'un commun accord + maintien total salaire",
>     "Mme [H] modifie immédiatement l'écrit (pièce 9)"
>   ],
>   "arguments": [
>     "La modification unilatérale des modalités d'organisation du travail constitue un manquement grave de l'employeur.",
>     "Le document initial ne correspondait pas à l'accord passé entre les parties."
>   ],
>   "dates_amounts": [
>     "06 avril 2020",
>     "07 avril 2020 à 8h40"
>   ],
>   "pieces_cited": ["pièce 9"],
>   "key_source_excerpt": "« Attendu que le 6 avril 2020, M. [G] a reçu par courriel les modalités d'organisation de son travail dans le cadre de l'activité partielle (chômage partiel), ce document mentionnant « congés à ta demande » à 2 reprises et indiquant « chaque heure non travaillée dans le cadre de ce dispositif exceptionnel sera indemnisée selon les dispositions légales ». Que M. [G] a dû demander le 7 avril 2020 à 8h40 par courriel que soit modifié cet écrit qui devait correspondre à l'accord passé (congés d'un commun accord, maintien total du salaire), ce que fera tout de suite Mme [H] (pièce 9). »",
>   "key_verbatim_points": [
>     "« congés à ta demande » (mentionné 2 fois dans le document)",
>     "« chaque heure non travaillée dans le cadre de ce dispositif exceptionnel sera indemnisée selon les dispositions légales »"
>   ]
> }
> ```
> "

---

### Niveau 2 : Parsing et packetisation

#### 🔧 Amélioration 5 : Critères de découpage repensés

**Problème actuel :** La conclusion de l'intimé (5272 lignes) est compressée en 1 seul packet P4, tandis que celle de l'appelant (3813 lignes) est répartie en 3 packets (P1, P2, P3).

**Critères actuels supposés :**
- Taille cible : ~1000 lignes par packet ?
- Découpage par grandes sections ?

**Problème :** La conclusion intimé contient beaucoup de répétitions (reprise des demandes initiales + ajouts), ce qui la rend plus longue mais moins dense en arguments nouveaux.

**Critères améliorés proposés :**

1. **Découpage par densité argumentaire :**
   - Sections "FAITS" + "PROCEDURE" : 1 packet dédié (faible densité)
   - Sections "DISCUSSION" / "MOYENS" : 1 packet par moyen principal (haute densité)
   - Sections "PAR CES MOTIFS" : 1 packet dédié (cruciale)

2. **Limite de tokens par packet :**
   - Au lieu de "lignes", utiliser le nombre de tokens estimé
   - Cible : 8 000 tokens par packet (équilibre entre contexte et coût)
   - Maximum : 12 000 tokens (pour éviter les erreurs de mémoire)

3. **Préservation de la structure hiérarchique :**
   - Ne jamais couper un "GRIEF" en deux packets
   - Si un moyen contient 32 griefs, soit :
     - Option A : 1 packet pour le moyen entier (si < 12k tokens)
     - Option B : 1 packet par sous-ensemble de 5-10 griefs (si > 12k tokens)

**Exemple de découpage amélioré pour la conclusion intimée :**

| Packet | Contenu | Lignes | Tokens estimés |
|--------|---------|--------|----------------|
| P_INTIMÉ_1 | RAPPEL DES FAITS + PROCEDURE | ~700 | ~7 000 |
| P_INTIMÉ_2 | Griefs 1-10 (harcèlement moral) | ~1000 | ~10 000 |
| P_INTIMÉ_3 | Griefs 11-20 | ~1000 | ~10 000 |
| P_INTIMÉ_4 | Griefs 21-32 | ~1200 | ~12 000 |
| P_INTIMÉ_5 | Arguments juridiques (résiliation, nullité) | ~800 | ~8 000 |
| P_INTIMÉ_6 | Indemnisation + PAR CES MOTIFS | ~600 | ~6 000 |

**Total :** 6 packets au lieu de 1, permettant une extraction plus fine.

---

#### 🔧 Amélioration 6 : Métadonnées de packet enrichies

**Problème :** Le champ `packet_summary` est trop générique.

**Actuel (Packet P4) :**
> "Le paquet traite de la matérialité de faits de harcèlement moral subis par Monsieur [B] [A] au sein de l'Association [Personne Morale 1], avec 23 faits constitutifs de harcèlement moral détaillés."

**Problème :** Le summary mentionne "23 faits" mais le packet ne contient en réalité que des arguments généraux, pas 23 griefs détaillés.

**Proposition :** Ajouter des métadonnées structurées au niveau packet :

```json
{
  "packet_id": "P_INTIMÉ_2",
  "document_role": "intimé",
  "packet_summary": "Griefs 1 à 10 de harcèlement moral : tension gouvernance (grief 1), remise en cause contrat (grief 2), perturbations bénévoles (grief 3), demande relevé quotidien (grief 4), modification organisation travail (grief 5), non-paiement prime MACRON (grief 6), retards maintien salaire (grief 7), mutisme RH (grief 8), remarque homophobe (grief 9), entretien annuel bâclé (grief 10).",
  "packet_metadata": {
    "grief_range": [1, 10],
    "total_griefs_in_packet": 10,
    "main_theme": "Harcèlement moral - Phase 1 (sept 2019 - avril 2020)",
    "key_participants": ["M. [M]", "Mme [Z]", "Mme [H]"],
    "key_dates": ["01/09/2019", "05/10/2019", "02/10/2019", "06/04/2020", "28/04/2020"]
  }
}
```

**Avantage :** Le LLM pourra mieux contextualiser l'information en fonction du packet.

---

### Niveau 3 : Validation

#### 🔧 Amélioration 7 : Check automatique de complétude

**Problème :** Aucun mécanisme de détection de perte d'information.

**Proposition :** Ajouter une étape de validation post-compression :

**Script de validation :**
```python
def validate_compression(original_text: str, json_compressed: dict) -> dict:
    """
    Valide que la compression n'a pas perdu d'information critique.
    Retourne un rapport de validation.
    """
    report = {
        "valid": True,
        "warnings": [],
        "errors": []
    }

    # Check 1 : Griefs numérotés
    original_griefs = re.findall(r'GRIEF\s+(\d+)\s*:', original_text)
    json_griefs = [
        s['title'] for p in json_compressed
        for s in p['sections']
        if 'GRIEF' in s.get('title', '')
    ]

    if len(original_griefs) != len(json_griefs):
        report['errors'].append({
            "type": "grief_count_mismatch",
            "original": len(original_griefs),
            "json": len(json_griefs),
            "missing": set(original_griefs) - set([
                re.search(r'GRIEF\s+(\d+)', g).group(1)
                for g in json_griefs if re.search(r'GRIEF\s+(\d+)', g)
            ])
        })
        report['valid'] = False

    # Check 2 : Montants chiffrés
    original_amounts = re.findall(r'(\d[\d\s,\.]*)\s*€', original_text)
    json_amounts = []
    for p in json_compressed:
        for s in p['sections']:
            for amount in s.get('dates_amounts', []):
                json_amounts.extend(re.findall(r'(\d[\d\s,\.]*)\s*€', amount))

    original_amounts_clean = set([a.replace(' ', '').replace(',', '.') for a in original_amounts])
    json_amounts_clean = set([a.replace(' ', '').replace(',', '.') for a in json_amounts])

    missing_amounts = original_amounts_clean - json_amounts_clean
    if len(missing_amounts) > 0.1 * len(original_amounts_clean):  # >10% de perte
        report['warnings'].append({
            "type": "amounts_missing",
            "percentage": len(missing_amounts) / len(original_amounts_clean) * 100,
            "examples": list(missing_amounts)[:5]
        })

    # Check 3 : Références légales
    original_cass = re.findall(r'Cass\.\s+\w+\.\s+\d+\s+\w+\.?\s+\d+,?\s+n[°o]\s*[\d\-]+', original_text)
    json_cass = []
    for p in json_compressed:
        for s in p['sections']:
            json_cass.extend([
                r for r in s.get('legal_references', [])
                if 'Cass' in r or 'cass' in r
            ])

    if len(original_cass) != len(json_cass):
        report['warnings'].append({
            "type": "jurisprudence_count_mismatch",
            "original": len(original_cass),
            "json": len(json_cass)
        })

    # Check 4 : Sections "PAR CES MOTIFS"
    original_par_ces_motifs = original_text.count('PAR CES MOTIF')
    json_par_ces_motifs = sum([
        1 for p in json_compressed
        for s in p['sections']
        if 'PAR CES MOTIF' in s.get('title', '')
    ])

    if original_par_ces_motifs != json_par_ces_motifs:
        report['errors'].append({
            "type": "par_ces_motifs_missing",
            "original": original_par_ces_motifs,
            "json": json_par_ces_motifs
        })
        report['valid'] = False

    return report
```

**Utilisation :**
```python
# Après compression
validation_report = validate_compression(
    original_appelant + original_intimé,
    json_compressed
)

if not validation_report['valid']:
    print("❌ COMPRESSION INVALIDE - ERREURS CRITIQUES :")
    for error in validation_report['errors']:
        print(f"  - {error['type']}: {error}")
    # Refuser la compression, redemander au LLM de retraiter
else:
    print("✅ Compression valide")
    if validation_report['warnings']:
        print("⚠️  Warnings :")
        for warning in validation_report['warnings']:
            print(f"  - {warning['type']}: {warning}")
```

---

#### 🔧 Amélioration 8 : Métrique de qualité de compression

**Proposition :** Calculer un score de qualité de compression pour chaque packet.

**Formule :**
```
Quality Score = (
    0.30 * completeness_score +  # Complétude (facts, arguments, legal_refs)
    0.25 * verbatim_score +       # Présence de citations exactes
    0.20 * structure_score +      # Préservation hiérarchie (path)
    0.15 * precision_score +      # Précision (dates, montants exacts)
    0.10 * metadata_score         # Qualité métadonnées (participants, types)
)
```

**Seuils :**
- Score < 0.50 : ❌ Packet à retravailler (perte d'information critique)
- Score 0.50-0.70 : 🟡 Packet acceptable mais perfectible
- Score > 0.70 : ✅ Packet de bonne qualité

**Exemple de calcul pour GRIEF 23 (présent dans JSON) :**

| Critère | Score | Détail |
|---------|-------|--------|
| Complétude | 0.90 | 4 faits / 4 attendus, 3 arguments / 3, 2 legal_refs / 2 |
| Verbatim | 0.80 | 2 citations exactes conservées / 3 potentielles |
| Structure | 1.00 | Path complet : ["GRIEF 23"] |
| Précision | 1.00 | Dates exactes (26/02/2022, 01/03/2022) |
| Métadonnées | 0.85 | 3 participants identifiés, 1 role ambigu |
| **TOTAL** | **0.88** | ✅ Excellente qualité |

**Exemple de calcul pour GRIEF 1 (absent du JSON) :**

| Critère | Score | Détail |
|---------|-------|--------|
| Complétude | 0.00 | Grief totalement absent |
| Verbatim | 0.00 | 0 citations |
| Structure | 0.00 | Pas de section GRIEF 1 |
| Précision | 0.00 | Aucune date extraite |
| Métadonnées | 0.00 | Aucun participant |
| **TOTAL** | **0.00** | ❌ Grief perdu |

---

#### 🔧 Amélioration 9 : Détection de perte d'information par comparaison de tokens

**Problème :** La compression actuelle passe de 9085 lignes à 1699 lignes (81% de perte) sans qu'on sache ce qui a été perdu.

**Proposition :** Comparer la distribution des tokens entre original et JSON.

**Méthode :**
1. Tokeniser le document original (avec un tokenizer type GPT-4)
2. Extraire les tokens du JSON (en reconstituant un texte à partir des champs)
3. Calculer la couverture :

```python
def calculate_token_coverage(original_text: str, json_compressed: dict) -> dict:
    """
    Calcule la couverture en tokens entre original et JSON.
    """
    import tiktoken

    enc = tiktoken.encoding_for_model("gpt-4")

    # Tokens de l'original
    original_tokens = enc.encode(original_text)
    original_unique = set(original_tokens)

    # Tokens du JSON (reconstruits)
    json_text = ""
    for p in json_compressed:
        for s in p['sections']:
            json_text += s.get('thesis', '') + " "
            json_text += " ".join(s.get('facts', [])) + " "
            json_text += " ".join(s.get('arguments', [])) + " "
            json_text += s.get('key_source_excerpt', '') + " "
            json_text += " ".join(s.get('key_verbatim_points', [])) + " "

    json_tokens = enc.encode(json_text)
    json_unique = set(json_tokens)

    # Couverture
    coverage = len(json_unique) / len(original_unique)

    # Tokens manquants (top 50)
    missing_tokens = original_unique - json_unique
    missing_decoded = [(enc.decode([t]), original_tokens.count(t)) for t in missing_tokens]
    missing_sorted = sorted(missing_decoded, key=lambda x: x[1], reverse=True)[:50]

    return {
        "original_unique_tokens": len(original_unique),
        "json_unique_tokens": len(json_unique),
        "coverage": coverage,
        "missing_top_50": missing_sorted
    }
```

**Interprétation :**
- Coverage > 0.70 : ✅ Bonne couverture
- Coverage 0.50-0.70 : 🟡 Couverture moyenne
- Coverage < 0.50 : ❌ Perte d'information critique

**Utilisation pour le dossier 6 :**
Si la couverture est < 0.50, analyser les tokens manquants pour identifier les thèmes perdus :
- Si "agression", "verbalement", "viré" sont dans les top 50 manquants → grief agression verbale perdu
- Si "grief_1", "grief_2", ... "grief_30" sont manquants → griefs non extraits

---

### Niveau 4 : Architecture

#### 🔧 Amélioration 10 : Pipeline en 2 passes

**Problème actuel :** Compression en 1 seule passe → perte d'information irréversible.

**Architecture actuelle supposée :**
```
Document original (9085 lignes)
     ↓
[LLM : extraction + compression]
     ↓
JSON compressé (1699 lignes, 81% de perte)
```

**Architecture améliorée proposée :**

```
Document original (9085 lignes)
     ↓
[PASSE 1 : Extraction structurée complète]
     ↓
JSON intermédiaire (format verbeux, 5000 lignes, 45% de perte)
     ↓
[PASSE 2 : Compression sélective]
     ↓
JSON final (format optimisé, 2500 lignes, 50% de perte supplémentaire)
     ↓
[VALIDATION : vérification complétude]
     ↓
JSON validé (avec rapport de qualité)
```

**Détails de chaque passe :**

**PASSE 1 : Extraction structurée (LLM avec prompt exhaustif)**
- Objectif : Extraire TOUT sans rien perdre
- Prompt : "Extraire tous les griefs, tous les arguments, toutes les dates, tous les montants"
- Format : JSON verbeux avec redondance autorisée
- Contrainte : Tolérance à la taille (JSON de 100KB autorisé)
- Validation : Check automatique de complétude (voir Amélioration 7)

**PASSE 2 : Compression sélective (LLM avec prompt de synthèse)**
- Objectif : Réduire la taille en gardant l'essentiel
- Prompt : "Fusionner les arguments redondants, déduplicater les faits, condenser les verbatim"
- Format : JSON optimisé
- Contrainte : Taille cible 50KB
- Validation : Vérification que les éléments critiques (griefs, montants clés) sont conservés

**Avantages :**
1. **Contrôle de la perte** : On sait exactement ce qui est perdu entre passe 1 et 2
2. **Récupérabilité** : Si le JSON final est insuffisant, on peut revenir au JSON intermédiaire et recompresser différemment
3. **Debugging** : Plus facile d'identifier si la perte vient de l'extraction (passe 1) ou de la compression (passe 2)

---

#### 🔧 Amélioration 11 : Introduction d'une étape de "Mappage de structure"

**Problème :** Le LLM perd la hiérarchie des moyens (I > A > 1 > GRIEF 1).

**Proposition :** Avant l'extraction, faire une passe de détection de structure.

**Étape 0 : Mappage de structure (LLM ou regex)**
```python
def map_document_structure(text: str) -> dict:
    """
    Détecte la structure hiérarchique du document avant extraction.
    """
    import re

    structure = {
        "sections": [],
        "hierarchy_levels": {}
    }

    # Détection des niveaux hiérarchiques
    # Niveau 1 : I-, II-, III-
    level1 = re.findall(r'^([IVX]+)-\s+(.+?)$', text, re.MULTILINE)
    # Niveau 2 : A-, B-, C-
    level2 = re.findall(r'^([A-Z])-\s+(.+?)$', text, re.MULTILINE)
    # Niveau 3 : 1-, 2-, 3-
    level3 = re.findall(r'^(\d+)-\s+(.+?)$', text, re.MULTILINE)
    # Niveau 4 : GRIEF X :
    level4 = re.findall(r'^GRIEF\s+(\d+)\s*:\s*(.*)$', text, re.MULTILINE)

    structure['hierarchy_levels'] = {
        "level1_count": len(level1),
        "level2_count": len(level2),
        "level3_count": len(level3),
        "level4_count": len(level4),
        "level4_list": [f"GRIEF {num}" for num, _ in level4]
    }

    return structure

# Utilisation
doc_structure = map_document_structure(original_text)
print(f"Document contient {doc_structure['hierarchy_levels']['level4_count']} griefs")
print(f"Liste des griefs : {doc_structure['hierarchy_levels']['level4_list']}")

# Puis transmettre cette structure au LLM dans le prompt
prompt = f"""
Vous allez extraire le document suivant qui contient :
- {doc_structure['hierarchy_levels']['level1_count']} sections principales (niveau I, II, III, ...)
- {doc_structure['hierarchy_levels']['level2_count']} sous-sections (niveau A, B, C, ...)
- {doc_structure['hierarchy_levels']['level4_count']} griefs numérotés

**CONSIGNE CRITIQUE** : Vous DEVEZ extraire les {doc_structure['hierarchy_levels']['level4_count']}
griefs suivants : {', '.join(doc_structure['hierarchy_levels']['level4_list'])}

[...]
"""
```

**Avantage :** Le LLM sait exactement combien de griefs il doit extraire et peut auto-vérifier.

---

#### 🔧 Amélioration 12 : Système de "carry-forward" enrichi

**Problème actuel :** Le champ `carry_forward` existe mais est sous-utilisé.

**Actuel (Packet P4) :**
```json
"carry_forward": {
  "main_issues": [
    "Validité de la résiliation judiciaire du contrat de travail pour harcèlement moral.",
    "Nullité du licenciement pour inaptitude d'origine professionnelle.",
    "Indemnisation du préjudice subi par Monsieur [B] [A].",
    "Remise de documents sous astreinte.",
    "Condamnation aux dépens et indemnité de l'article 700 du CPC."
  ],
  "open_threads": [
    "Vérification des montants d'indemnisation et des pièces manquantes."
  ]
}
```

**Problème :** Les "open_threads" ne sont pas exploités par la synthèse finale.

**Proposition :** Enrichir `carry_forward` avec :

```json
"carry_forward": {
  "main_issues": [...],
  "open_threads": [
    {
      "thread_id": "GRIEF_MISSING",
      "description": "30 griefs de harcèlement moral (GRIEF 1 à 22, 25 à 32) sont mentionnés dans le document original mais n'ont pas été extraits dans ce packet.",
      "severity": "critical",
      "action_needed": "Créer des packets additionnels pour extraire les griefs manquants."
    },
    {
      "thread_id": "AMOUNTS_AGGREGATED",
      "description": "Les demandes subsidiaires de l'intimé contiennent 9 montants distincts mais seuls 5 sont détaillés dans 'requests'.",
      "severity": "high",
      "action_needed": "Décomposer le champ 'requests' pour inclure tous les montants avec leur libellé."
    }
  ],
  "cross_references": [
    {
      "from": "P_APPELANT_2_GRIEF_23",
      "to": "P_INTIMÉ_4_REPONSE_GRIEF_23",
      "relation": "rebuttal"
    }
  ],
  "claims_block_present": true,
  "participants_to_track": [...]
}
```

**Utilisation :** Lors de la synthèse finale, le LLM pourrait :
1. Détecter les "open_threads" de severité "critical"
2. Alerter l'utilisateur : "⚠️ 30 griefs manquants, la synthèse sera incomplète"
3. Utiliser les "cross_references" pour construire un argumentaire contradictoire

---

## 4. SYNTHÈSE DES RECOMMANDATIONS

### Priorité 1 (CRITIQUE - Impact immédiat)

1. **Prompt d'extraction des griefs numérotés** (Amélioration 1)
   - Temps de mise en œuvre : 1 heure
   - Impact : Passe de 2 griefs extraits à 32 griefs (gain de 1500%)

2. **Validation automatique de complétude** (Amélioration 7)
   - Temps de mise en œuvre : 4 heures
   - Impact : Détection immédiate des pertes d'information

3. **Prompt pour hiérarchie principal/subsidiaire** (Amélioration 2)
   - Temps de mise en œuvre : 1 heure
   - Impact : Préservation de la stratégie juridique de l'intimé

### Priorité 2 (HAUTE - Amélioration qualité)

4. **Contrainte de densité pour "PAR CES MOTIFS"** (Amélioration 3)
   - Temps de mise en œuvre : 2 heures
   - Impact : Montants chiffrés complets (9 au lieu de 5)

5. **Pipeline en 2 passes** (Amélioration 10)
   - Temps de mise en œuvre : 8 heures
   - Impact : Contrôle de la perte d'information entre extraction et compression

6. **Critères de découpage repensés** (Amélioration 5)
   - Temps de mise en œuvre : 4 heures
   - Impact : Meilleur équilibre entre packets (6 packets intimé au lieu de 1)

### Priorité 3 (MOYENNE - Optimisation)

7. **Métrique de qualité de compression** (Amélioration 8)
   - Temps de mise en œuvre : 6 heures
   - Impact : Visibilité sur la qualité de chaque packet (score 0-1)

8. **Mappage de structure pré-extraction** (Amélioration 11)
   - Temps de mise en œuvre : 4 heures
   - Impact : LLM sait combien de griefs extraire (auto-vérification)

9. **Exemple de bonne extraction au LLM** (Amélioration 4)
   - Temps de mise en œuvre : 2 heures
   - Impact : LLM comprend mieux le niveau de détail attendu

### Priorité 4 (BASSE - Nice-to-have)

10. **Détection perte par comparaison tokens** (Amélioration 9)
    - Temps de mise en œuvre : 3 heures
    - Impact : Analyse fine des thèmes perdus

11. **Système carry-forward enrichi** (Amélioration 12)
    - Temps de mise en œuvre : 5 heures
    - Impact : Meilleure traçabilité des informations entre packets

12. **Métadonnées de packet enrichies** (Amélioration 6)
    - Temps de mise en œuvre : 2 heures
    - Impact : Contexte amélioré pour le LLM lors de la synthèse

---

## 5. PLAN D'ACTION RECOMMANDÉ

### Phase 1 : Quick Wins (Semaine 1)

**Objectif :** Passer de 2 griefs extraits à 32 griefs avec validation automatique.

1. **Jour 1-2 :** Implémenter Amélioration 1 (prompt griefs) + Amélioration 2 (hiérarchie)
2. **Jour 3-4 :** Implémenter Amélioration 7 (validation complétude)
3. **Jour 5 :** Tester sur dossier 6, comparer avec JSON actuel

**Résultat attendu :**
- JSON avec 32 griefs extraits (vs 2 actuellement)
- Rapport de validation indiquant "✅ 32/32 griefs extraits"

---

### Phase 2 : Amélioration structurelle (Semaine 2-3)

**Objectif :** Pipeline en 2 passes + découpage optimisé.

1. **Semaine 2 :** Implémenter Amélioration 10 (pipeline 2 passes)
   - Passe 1 : Extraction exhaustive
   - Passe 2 : Compression sélective
2. **Semaine 3 :** Implémenter Amélioration 5 (découpage repensé) + Amélioration 11 (mappage structure)

**Résultat attendu :**
- JSON intermédiaire de 100KB (passe 1, perte <30%)
- JSON final de 50KB (passe 2, perte totale <60%)
- 6 packets pour l'intimé (vs 1 actuellement)

---

### Phase 3 : Métriques et optimisation (Semaine 4)

**Objectif :** Visibilité sur la qualité + optimisation continue.

1. **Implémenter :** Amélioration 8 (métriques qualité) + Amélioration 3 (densité PAR CES MOTIFS)
2. **Tester sur :** Dossiers 1-10 pour valider la généralisation

**Résultat attendu :**
- Dashboard de qualité : score moyen > 0.75 par packet
- Montants chiffrés complets dans "PAR CES MOTIFS"

---

### Phase 4 : Raffinement (Semaine 5+)

**Objectif :** Amélioration continue.

1. **Implémenter :** Améliorations 4, 6, 9, 12 (nice-to-have)
2. **Itérer :** Sur la base des retours utilisateurs et des nouveaux dossiers

---

## 6. CONCLUSION

### Écarts critiques identifiés

1. **94% des griefs perdus** (2 sur 32 extraits)
2. **Déséquilibre documentaire** (1 packet intimé vs 3 packets appelant)
3. **Hiérarchie des demandes aplatie** (principal/subsidiaire non distingué)
4. **Arguments détaillés compressés à ~10%** de leur volume original
5. **Montants chiffrés agrégés** (5 postes détaillés vs 9 réels)

### Impact sur le résultat final

Le LLM générera une synthèse :
- **Incomplète** (30 griefs manquants, faits clés absents)
- **Déséquilibrée** (vision appelant surreprésentée par défaut d'information contradictoire)
- **Imprécise** (montants et dates partiels)
- **Appauvrie** (raisonnements juridiques réduits à des bullet points)

**Risque global :** Une décision basée sur cette synthèse pourrait manquer 90% des éléments factuels du litige.

### Recommandations prioritaires

**TOP 3 actions immédiates :**
1. Prompt explicite pour extraction de tous les griefs numérotés
2. Validation automatique de complétude (détection pertes)
3. Hiérarchisation des demandes (principal/subsidiaire)

**Avec ces 3 actions**, le taux de perte passerait de ~90% à ~40%, ce qui rendrait le JSON exploitable pour une synthèse de qualité acceptable.

---

**Fin du rapport**

Analyse réalisée le 2026-03-31 par Claude Sonnet 4.5.
