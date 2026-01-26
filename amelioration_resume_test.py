"""
Test d'amélioration du résumé de conclusions
Découpage déterministe + traitement parallèle des sections
"""

import os
import re
import time
import json
import concurrent.futures
from dotenv import load_dotenv
from mistralai import Mistral

# Charger les variables d'environnement
load_dotenv()

# Configuration
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MODEL = "mistral-medium-2508"  # Modèle assistant numérique


# =============================================================================
# PARTIE 1 : DÉCOUPAGE DÉTERMINISTE DES CONCLUSIONS
# =============================================================================

def decouper_conclusions(texte: str) -> dict:
    """
    Découpe une conclusion juridique en ses différentes sections :
    - en_tete : parties, juridiction, etc.
    - faits : section FAITS / FAITS ET PROCEDURES
    - moyens : section DISCUSSION / MOYENS / EN DROIT
    - pretentions : section PAR CES MOTIFS / DISPOSITIF
    - pieces : liste des pièces (optionnel)

    Retourne un dictionnaire avec les sections identifiées.
    """

    # Normaliser les retours à la ligne
    texte = texte.replace('\r\n', '\n').replace('\r', '\n')

    # Patterns pour identifier les débuts de sections
    # On cherche ces marqueurs en début de ligne ou après des espaces
    # Patterns enrichis suite à l'analyse des dossiers réels
    patterns = {
        'faits': [
            # Formats avec numérotation A. ou I.
            r'\n\s*A\.\s*FAITS\s+ET\s+PROC[EÉ]DURES?\s*\n',
            r'\n\s*I\.\s*FAITS\s+ET\s+PROC[EÉ]DURES?\s*\n',
            r'\n\s*I\.\s*Faits\s+et\s+proc[eé]dures?\s*\n',  # minuscules
            # Formats avec tiret (court ou long)
            r'\n\s*I\s*[–\-]\s*RAPPEL\s+DES\s+FAITS(?:\s+ET\s+DE\s+LA\s+PROC[EÉ]DURE)?\s*\n',
            r'\n\s*I\s*[–\-]\s*FAITS\s+ET\s+PROC[EÉ]DURES?\s*\n',
            # Formats simples
            r'\n\s*FAITS\s+ET\s+PROC[EÉ]DURES?\s*\n',
            r'\n\s*I[\.\-\s]+(?:LES\s+)?FAITS\s*\n',
            r'\n\s*RAPPEL\s+DES\s+FAITS\s*\n',
            r'\n\s*EXPOS[EÉ]\s+DES\s+FAITS\s*\n',
            r'\n\s*LES\s+FAITS\s*\n',
        ],
        'moyens': [
            # Formats avec numérotation II. ou B.
            r'\n\s*II\.\s*DISCUSSION\s*\n',
            r'\n\s*II[\.\-]\s*Discussion\s*\n',  # minuscule
            r'\n\s*B\.\s*DISCUSSION\s*\n',
            # Formats avec tiret (court ou long)
            r'\n\s*II\s*[–\-]\s*DISCUSSION\s*\n',
            # Typos courantes (11 au lieu de II)
            r'\n\s*1{1,2}\.\s*Discussion\s*\n',
            # Formats simples
            r'\n\s*DISCUSSION\s*\n',
            r'\n\s*II[\.\-\s]+(?:EN\s+)?DROIT\s*\n',
            r'\n\s*EN\s+DROIT\s*\n',
            r'\n\s*MOYENS\s*\n',
            r'\n\s*(?:LES\s+)?MOYENS\s+DE\s+DROIT\s*\n',
            r'\n\s*ARGUMENTAIRE\s*\n',
        ],
        'pretentions': [
            r'\n\s*PAR\s+CES\s+MOTIFS\s*',
            r'\n\s*Par\s+ces\s+motifs\s*,?\s*(?:plaise\s+[aà]\s+la\s+cour)?\s*,?\s*\n',  # minuscule
            r'\n\s*EN\s+CONS[EÉ]QUENCE\s*\n',
            r'\n\s*IL\s+(?:EST\s+)?PLA[IÎ]T?\s+[AÀ]\s+LA\s+(?:COUR|JURIDICTION)\s*',
            r'\n\s*PLAISE\s+[AÀ]\s+LA\s+(?:COUR|JURIDICTION)\s*',
            r'\n\s*DISPOSITIF\s*\n',
            r'\n\s*C\'EST\s+POURQUOI\s*\n',
            r'\n\s*AU\s+REGARD\s+DE\s+CE\s+QUI\s+PR[EÉ]C[EÈ]DE\s*',
        ],
        'pieces': [
            r'\n\s*[AÀ]\s+l\'appui\s+de\s+la\s+demande',
            r'\n\s*PI[EÈ]CES?\s+PRODUITES?\s+AUX\s+D[EÉ]BATS',
            r'\n\s*Liste\s+des\s+pi[eè]ces',
            r'\n\s*Pi[eè]ces?\s+communiqu[eé]es?\s*:',
            r'\n\s*BORDEREAU',
            r'\n\s*LISTE\s+DES\s+PI[EÈ]CES',
        ]
    }

    # Trouver les positions des sections
    positions = {}

    for section, pattern_list in patterns.items():
        for pattern in pattern_list:
            # Pour les prétentions, chercher la DERNIÈRE occurrence
            # (les conclusions d'appel citent souvent la décision contestée avec "PAR CES MOTIFS")
            if section == 'pretentions':
                matches = list(re.finditer(pattern, texte, re.IGNORECASE))
                if matches:
                    # Prendre la dernière occurrence
                    positions[section] = matches[-1].start()
                    break
            else:
                match = re.search(pattern, texte, re.IGNORECASE)
                if match:
                    positions[section] = match.start()
                    break

    # Déterminer l'ordre des sections trouvées
    sections_ordonnees = sorted(positions.items(), key=lambda x: x[1])

    # Extraire le contenu de chaque section
    resultat = {
        'en_tete': '',
        'faits': '',
        'moyens': '',
        'pretentions': '',
        'pieces': '',
        'sections_trouvees': list(positions.keys())
    }

    # L'en-tête est tout ce qui précède la première section identifiée
    if sections_ordonnees:
        resultat['en_tete'] = texte[:sections_ordonnees[0][1]].strip()
    else:
        # Si aucune section n'est trouvée, tout est considéré comme en-tête
        resultat['en_tete'] = texte.strip()
        return resultat

    # Extraire chaque section
    for i, (section_name, start_pos) in enumerate(sections_ordonnees):
        # Trouver la fin de cette section (début de la suivante ou fin du texte)
        if i + 1 < len(sections_ordonnees):
            end_pos = sections_ordonnees[i + 1][1]
        else:
            end_pos = len(texte)

        resultat[section_name] = texte[start_pos:end_pos].strip()

    return resultat


# =============================================================================
# PARTIE 1b : DÉCOUPAGE ASSISTÉ PAR LLM (FALLBACK)
# =============================================================================

# Description des règles pour aider le LLM
REGLES_SECTIONS = """
## Règles de découpage des conclusions juridiques

Une conclusion juridique française contient généralement ces sections dans cet ordre :

### 1. EN-TÊTE (début du document)
Contient : juridiction, numéro RG, parties (POUR/CONTRE), avocats, "PLAISE À LA COUR"

### 2. FAITS (ou FAITS ET PROCÉDURE)
Marqueurs connus :
- "A. FAITS ET PROCÉDURES" ou "I. FAITS ET PROCÉDURES"
- "I – RAPPEL DES FAITS" (avec tiret)
- "EXPOSÉ DES FAITS"
- Parfois implicite après "Le ministère public a l'honneur d'exposer :"
Contenu : chronologie des événements, contexte factuel, historique procédural

### 3. DISCUSSION (ou MOYENS / EN DROIT)
Marqueurs connus :
- "II. DISCUSSION" ou "II – DISCUSSION"
- "EN DROIT", "MOYENS", "ARGUMENTAIRE"
- Parfois numéroté "11." (typo)
Contenu : arguments juridiques, références aux articles de loi, jurisprudence

### 4. PRÉTENTIONS (ou DISPOSITIF)
Marqueurs connus :
- "PAR CES MOTIFS" (le plus fréquent)
- "Par ces motifs, plaise à la cour,"
- "EN CONSÉQUENCE"
Contenu : demandes formelles (DIRE ET JUGER, CONDAMNER, INFIRMER, etc.)

### 5. PIÈCES (optionnel, à la fin)
Marqueurs connus :
- "Liste des pièces", "Pièces communiquées"
- "PIÈCES PRODUITES AUX DÉBATS"
- "À l'appui de la demande"
Contenu : liste numérotée des documents produits
"""


def decouper_conclusions_llm(texte: str, sections_manquantes: list = None) -> dict:
    """
    Utilise le LLM pour découper les conclusions quand les regex échouent.
    Le LLM est assisté par les règles connues.

    Args:
        texte: Le texte des conclusions
        sections_manquantes: Liste des sections non trouvées par regex (ex: ['faits', 'moyens'])

    Returns:
        Dictionnaire avec les sections identifiées
    """
    if not MISTRAL_API_KEY:
        raise ValueError("La clé API Mistral n'est pas configurée.")

    sections_a_trouver = sections_manquantes or ['faits', 'moyens', 'pretentions']

    prompt_system = f"""Tu es un expert en analyse de documents juridiques français.

{REGLES_SECTIONS}

## Ta tâche
Analyse le texte de conclusions juridiques fourni et identifie les sections demandées.

IMPORTANT :
- Retourne UNIQUEMENT un JSON valide, sans texte avant ou après
- Pour chaque section, donne l'indice de caractère de DÉBUT dans le texte original
- Si une section n'existe pas, mets null
- Les indices doivent correspondre exactement aux positions dans le texte

Format de réponse attendu :
{{
    "faits": {{"debut": <indice_int_ou_null>, "marqueur_trouve": "<texte du marqueur ou description>"}},
    "moyens": {{"debut": <indice_int_ou_null>, "marqueur_trouve": "<texte du marqueur ou description>"}},
    "pretentions": {{"debut": <indice_int_ou_null>, "marqueur_trouve": "<texte du marqueur ou description>"}}
}}
"""

    # Limiter le texte pour le prompt (garder début et contexte)
    texte_tronque = texte[:15000] if len(texte) > 15000 else texte

    prompt_user = f"""Voici le texte des conclusions à analyser.
Trouve les sections suivantes : {', '.join(sections_a_trouver)}

TEXTE DES CONCLUSIONS :
---
{texte_tronque}
---

Retourne le JSON avec les positions de début de chaque section."""

    client = Mistral(api_key=MISTRAL_API_KEY)

    response = client.chat.complete(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ]
    )

    reponse_llm = response.choices[0].message.content

    # Parser le JSON retourné
    try:
        # Nettoyer la réponse (enlever ```json si présent)
        reponse_clean = reponse_llm.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        reponse_clean = reponse_clean.strip()

        positions_llm = json.loads(reponse_clean)
        return positions_llm
    except Exception as e:
        print(f"  ⚠ Erreur parsing réponse LLM: {e}")
        print(f"  Réponse brute: {reponse_llm[:500]}")
        return {}


def decouper_conclusions_hybride(texte: str, utiliser_llm_fallback: bool = True) -> dict:
    """
    Approche hybride :
    1. Tente d'abord le découpage regex (rapide, gratuit)
    2. Si des sections importantes manquent, utilise le LLM en fallback

    Args:
        texte: Le texte des conclusions
        utiliser_llm_fallback: Si True, utilise le LLM quand des sections manquent

    Returns:
        Dictionnaire avec les sections identifiées
    """
    # Étape 1 : Découpage regex
    resultat = decouper_conclusions(texte)
    sections_trouvees = resultat['sections_trouvees']

    # Sections minimales requises pour un bon résumé
    sections_requises = ['faits', 'moyens', 'pretentions']
    sections_manquantes = [s for s in sections_requises if s not in sections_trouvees]

    # Si toutes les sections importantes sont trouvées, on retourne
    if not sections_manquantes:
        resultat['methode'] = 'regex'
        return resultat

    print(f"  ⚠ Sections manquantes après regex: {sections_manquantes}")

    # Étape 2 : Fallback LLM si activé
    if not utiliser_llm_fallback:
        resultat['methode'] = 'regex_partiel'
        return resultat

    print(f"  → Utilisation du LLM pour trouver: {sections_manquantes}")

    try:
        positions_llm = decouper_conclusions_llm(texte, sections_manquantes)

        # Fusionner les résultats LLM avec les résultats regex
        for section in sections_manquantes:
            if section in positions_llm and positions_llm[section]:
                info = positions_llm[section]
                if info.get('debut') is not None:
                    debut = info['debut']
                    # Trouver la fin (prochaine section ou fin du texte)
                    # On utilise les positions déjà connues
                    positions_connues = []
                    for s in sections_requises:
                        if s in resultat and resultat[s]:
                            # Trouver la position de cette section dans le texte
                            match = re.search(re.escape(resultat[s][:50]), texte)
                            if match:
                                positions_connues.append(match.start())

                    # Trouver la fin
                    fins_possibles = [p for p in positions_connues if p > debut]
                    fin = min(fins_possibles) if fins_possibles else len(texte)

                    resultat[section] = texte[debut:fin].strip()
                    if section not in resultat['sections_trouvees']:
                        resultat['sections_trouvees'].append(section)
                    print(f"  ✓ Section '{section}' trouvée par LLM (pos: {debut})")

        resultat['methode'] = 'hybride'

    except Exception as e:
        print(f"  ✗ Erreur LLM fallback: {e}")
        resultat['methode'] = 'regex_partiel'

    return resultat


# =============================================================================
# PARTIE 2 : CHARGEMENT DES PROMPTS
# =============================================================================

def charger_prompt(nom_fichier: str) -> str:
    """Charge un prompt depuis un fichier markdown."""
    try:
        with open(nom_fichier, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier de prompt '{nom_fichier}' n'a pas été trouvé.")


def charger_tous_les_prompts() -> dict:
    """Charge tous les prompts nécessaires."""
    return {
        'faits': charger_prompt('resume_faits.md'),
        'moyens': charger_prompt('resume_moyens.md'),
        'pretentions': charger_prompt('resume_pretentions.md'),
        'synthese_faits_procedure': charger_prompt('synthese_faits_procedure.md'),
    }


# =============================================================================
# PARTIE 3 : APPELS AU LLM
# =============================================================================

def appeler_llm(system_prompt: str, user_content: str, model: str = MODEL) -> str:
    """
    Appelle le LLM Mistral avec un prompt système et un contenu utilisateur.
    """
    if not MISTRAL_API_KEY:
        raise ValueError("La clé API Mistral n'est pas configurée.")

    client = Mistral(api_key=MISTRAL_API_KEY)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    response = client.chat.complete(
        model=model,
        messages=messages
    )

    return response.choices[0].message.content


def resumer_section(section_name: str, section_content: str, prompt: str) -> tuple[str, str, float]:
    """
    Résume une section avec le prompt approprié.
    Retourne (nom_section, résumé, temps_execution).
    """
    start_time = time.time()

    if not section_content.strip():
        return (section_name, f"[Section '{section_name}' non trouvée dans le document]", 0.0)

    try:
        resume = appeler_llm(prompt, section_content)
        elapsed = time.time() - start_time
        return (section_name, resume, elapsed)
    except Exception as e:
        elapsed = time.time() - start_time
        return (section_name, f"[Erreur lors du résumé de '{section_name}': {str(e)}]", elapsed)


# =============================================================================
# PARTIE 4 : TRAITEMENT PARALLÈLE
# =============================================================================

def resumer_conclusions_parallele(texte_conclusions: str, prompts: dict, utiliser_hybride: bool = True, verification_finale: bool = True) -> dict:
    """
    Résume une conclusion en utilisant le découpage (hybride ou regex seul)
    et le traitement parallèle des sections.

    Args:
        texte_conclusions: Le texte des conclusions à résumer
        prompts: Dictionnaire des prompts pour chaque section
        utiliser_hybride: Si True, utilise l'approche hybride (regex + LLM fallback)
        verification_finale: Si True, fait un passage LLM final pour vérifier/nettoyer le format

    Retourne un dictionnaire avec :
    - sections_decoupees : les sections brutes
    - resumes : les résumés de chaque section
    - resume_brut : le résumé avant vérification
    - resume_final : le résumé assemblé (après vérification si activée)
    - temps : les temps d'exécution
    - methode_decoupage : 'regex', 'hybride' ou 'regex_partiel'
    """

    print("=" * 60)
    if utiliser_hybride:
        print("ÉTAPE 1 : Découpage HYBRIDE des conclusions (regex + LLM fallback)")
    else:
        print("ÉTAPE 1 : Découpage REGEX des conclusions")
    print("=" * 60)

    start_decoupage = time.time()
    if utiliser_hybride:
        sections = decouper_conclusions_hybride(texte_conclusions, utiliser_llm_fallback=True)
    else:
        sections = decouper_conclusions(texte_conclusions)
        sections['methode'] = 'regex'
    temps_decoupage = time.time() - start_decoupage

    print(f"\nSections trouvées : {sections['sections_trouvees']}")
    print(f"Méthode utilisée : {sections.get('methode', 'regex')}")
    print(f"Temps de découpage : {temps_decoupage:.3f}s")

    for section in ['en_tete', 'faits', 'moyens', 'pretentions']:
        longueur = len(sections.get(section, ''))
        print(f"  - {section}: {longueur} caractères")

    print("\n" + "=" * 60)
    print("ÉTAPE 2 : Résumé parallèle des sections (faits, moyens, prétentions)")
    print("=" * 60)

    # Préparer les tâches pour le traitement parallèle
    taches = [
        ('faits', sections.get('faits', ''), prompts['faits']),
        ('moyens', sections.get('moyens', ''), prompts['moyens']),
        ('pretentions', sections.get('pretentions', ''), prompts['pretentions']),
    ]

    resumes = {}
    temps_sections = {}

    start_parallele = time.time()

    # Exécution parallèle avec ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(resumer_section, nom, contenu, prompt): nom
            for nom, contenu, prompt in taches
        }

        for future in concurrent.futures.as_completed(futures):
            nom_section, resume, temps_exec = future.result()
            resumes[nom_section] = resume
            temps_sections[nom_section] = temps_exec
            print(f"  ✓ Section '{nom_section}' résumée en {temps_exec:.2f}s")

    temps_parallele_total = time.time() - start_parallele

    print(f"\nTemps total parallèle : {temps_parallele_total:.2f}s")
    print(f"(Économie vs séquentiel : {sum(temps_sections.values()) - temps_parallele_total:.2f}s)")

    print("\n" + "=" * 60)
    print("ÉTAPE 3 : Assemblage du résumé")
    print("=" * 60)

    # Assembler le résumé
    resume_brut = assembler_resume(sections['en_tete'], resumes)
    print(f"\nRésumé brut assemblé : {len(resume_brut)} caractères")

    # Étape 4 : Vérification finale (optionnelle)
    temps_verification = 0
    if verification_finale:
        print("\n" + "=" * 60)
        print("ÉTAPE 4 : Vérification et nettoyage du format (LLM)")
        print("=" * 60)

        start_verif = time.time()
        resume_final = verifier_et_formater_resume(resume_brut)
        temps_verification = time.time() - start_verif

        print(f"\n  ✓ Vérification terminée en {temps_verification:.2f}s")
        print(f"  Résumé final : {len(resume_final)} caractères")
    else:
        resume_final = resume_brut

    temps_total = temps_decoupage + temps_parallele_total + temps_verification

    return {
        'sections_decoupees': sections,
        'resumes': resumes,
        'resume_brut': resume_brut,
        'resume_final': resume_final,
        'methode_decoupage': sections.get('methode', 'regex'),
        'temps': {
            'decoupage': temps_decoupage,
            'sections': temps_sections,
            'parallele_total': temps_parallele_total,
            'verification': temps_verification,
            'total': temps_total
        }
    }


def assembler_resume(en_tete: str, resumes: dict) -> str:
    """
    Assemble les résumés des différentes sections en un résumé final structuré.
    Format fluide avec numérotation cohérente :
    - EN-TÊTE (parties, juridiction)
    - I - Résumé des faits
    - II - Résumé des moyens
    - III - Résumé des prétentions
    """

    # Extraire les informations clés de l'en-tête pour le résumé
    resume_entete = extraire_info_entete(en_tete)

    parties = [
        "# RÉSUMÉ DE CONCLUSION",
        "",
        "## EN-TÊTE",
        "",
        "```",
        resume_entete,
        "```",
        "",
        resumes.get('faits', '## I - RÉSUMÉ DES FAITS\n\n[Section faits non disponible]'),
        "",
        resumes.get('moyens', '## II - RÉSUMÉ DES MOYENS\n\n[Section moyens non disponible]'),
        "",
        resumes.get('pretentions', '## III - RÉSUMÉ DES PRÉTENTIONS\n\n[Section prétentions non disponible]'),
    ]

    return "\n".join(parties)


def extraire_info_entete(en_tete: str) -> str:
    """
    Extrait et formate les informations de l'en-tête.
    L'en-tête sera affiché dans un bloc de code pour préserver le formatage.
    """
    lignes = en_tete.strip().split('\n')
    lignes_nettoyees = [l.strip() for l in lignes if l.strip()]
    return '\n'.join(lignes_nettoyees)


def verifier_et_formater_resume(resume_brut: str) -> str:
    """
    Passage final LLM pour vérifier et nettoyer le format du résumé.

    Vérifie :
    - Cohérence de la structure (I, II, III)
    - Suppression des redondances
    - Nettoyage des artefacts de formatage
    - Clarté et lisibilité
    """
    if not MISTRAL_API_KEY:
        print("  ⚠ Clé API manquante, retour du résumé brut")
        return resume_brut

    prompt_system = """Tu es un expert en relecture et mise en forme de documents juridiques.

Ta tâche est de vérifier et nettoyer le résumé de conclusions juridiques fourni.

## Règles de vérification :

1. **Structure** : Le résumé doit avoir cette structure exacte :
   - # RÉSUMÉ DE CONCLUSION
   - ## EN-TÊTE (avec les parties, juridiction)
   - ## I - RÉSUMÉ DES FAITS
   - ## II - RÉSUMÉ DES MOYENS
   - ## III - RÉSUMÉ DES PRÉTENTIONS

2. **Nettoyage** :
   - Supprimer les lignes vides excessives
   - Corriger les numérotations incohérentes (ex: "### I" puis "## II")
   - Supprimer les balises HTML parasites (<u>, </u>, etc.)
   - Supprimer les artefacts de formatage étranges

3. **Détection et fusion des DOUBLONS** (TRÈS IMPORTANT) :
   - Si deux sous-sections ont un contenu très similaire ou identique, les FUSIONNER en une seule
   - Si deux paragraphes répètent les mêmes arguments/faits, garder uniquement la version la plus complète
   - Vérifier que chaque information n'apparaît qu'une seule fois dans le résumé
   - Les titres de sous-sections similaires doivent être fusionnés (ex: "I - Sur X" et "II - Sur X" → garder un seul)

4. **Cohérence** :
   - Les prétentions doivent être les DEMANDES de la partie (RECEVOIR, INFIRMER, CONDAMNER, etc.)
   - Pas de reproduction de décisions antérieures dans les prétentions
   - L'en-tête doit identifier clairement les parties et la juridiction
   - Renuméroter les sous-sections si nécessaire après fusion (I, II, III ou A, B, C)

5. **Préserver** :
   - Le contenu substantiel (ne pas résumer davantage, sauf pour éliminer les doublons)
   - Les références aux pièces et articles de loi
   - Les noms anonymisés [X], [Y], etc.

## Format de sortie :
Retourne UNIQUEMENT le résumé corrigé en markdown, sans commentaires ni explications."""

    prompt_user = f"""Voici le résumé à vérifier et nettoyer :

{resume_brut}

Retourne le résumé corrigé et proprement formaté."""

    try:
        client = Mistral(api_key=MISTRAL_API_KEY)

        response = client.chat.complete(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ]
        )

        resume_corrige = response.choices[0].message.content

        # Nettoyer si le LLM a ajouté des balises markdown de code
        if resume_corrige.startswith("```"):
            lignes = resume_corrige.split("\n")
            # Enlever première et dernière ligne si ce sont des ```
            if lignes[0].startswith("```"):
                lignes = lignes[1:]
            if lignes and lignes[-1].strip() == "```":
                lignes = lignes[:-1]
            resume_corrige = "\n".join(lignes)

        return resume_corrige.strip()

    except Exception as e:
        print(f"  ⚠ Erreur lors de la vérification LLM: {e}")
        return resume_brut


# =============================================================================
# PARTIE 5 : PROGRAMME PRINCIPAL DE TEST
# =============================================================================

def tester_decoupage_fichiers():
    """Teste le découpage sur tous les fichiers Dossier_* disponibles."""

    import glob

    fichiers = glob.glob("Dossier_*.txt")
    fichiers = [f for f in fichiers if "Dossier_6" not in f]  # Exclure le fichier trop volumineux

    print("\n" + "=" * 70)
    print("   TEST DE DÉCOUPAGE SUR TOUS LES DOSSIERS")
    print("=" * 70)

    resultats = []

    for fichier in sorted(fichiers):
        print(f"\n{'─' * 50}")
        print(f"📄 {fichier}")
        print(f"{'─' * 50}")

        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                texte = f.read()

            # Test regex seul
            sections_regex = decouper_conclusions(texte)
            sections_regex['methode'] = 'regex'

            # Test hybride
            sections_hybride = decouper_conclusions_hybride(texte, utiliser_llm_fallback=True)

            print(f"\n  REGEX seul    : {sections_regex['sections_trouvees']}")
            print(f"  HYBRIDE       : {sections_hybride['sections_trouvees']} (méthode: {sections_hybride.get('methode', '?')})")

            resultats.append({
                'fichier': fichier,
                'regex': sections_regex['sections_trouvees'],
                'hybride': sections_hybride['sections_trouvees'],
                'methode': sections_hybride.get('methode', 'regex')
            })

        except Exception as e:
            print(f"  ✗ Erreur: {e}")

    # Résumé
    print("\n" + "=" * 70)
    print("   RÉSUMÉ DES TESTS")
    print("=" * 70)

    for r in resultats:
        regex_ok = len(r['regex']) >= 3
        hybride_ok = len(r['hybride']) >= 3
        status = "✓" if hybride_ok else "⚠"
        print(f"{status} {r['fichier']}: regex={len(r['regex'])} sections, hybride={len(r['hybride'])} ({r['methode']})")

    return resultats


def main():
    """Fonction principale de test."""

    print("\n" + "=" * 70)
    print("   TEST D'AMÉLIORATION DU RÉSUMÉ DE CONCLUSIONS")
    print("   Approche HYBRIDE : Regex + LLM fallback")
    print("=" * 70 + "\n")

    # -------------------------------------------------------------------------
    # TEST 0 : Découpage sur tous les fichiers disponibles
    # -------------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("TEST 0 : Comparaison Regex vs Hybride sur tous les dossiers")
    print("-" * 70)

    tester_decoupage_fichiers()

    # -------------------------------------------------------------------------
    # TEST 1 : Résumé complet sur un fichier standard
    # -------------------------------------------------------------------------
    fichier_conclusions = "Dossier_4_conclusion_appelante.txt"

    try:
        with open(fichier_conclusions, 'r', encoding='utf-8') as f:
            texte_conclusions = f.read()
        print(f"\n✓ Fichier chargé : {fichier_conclusions}")
        print(f"  Taille : {len(texte_conclusions)} caractères")
    except FileNotFoundError:
        print(f"✗ Erreur : Le fichier '{fichier_conclusions}' n'a pas été trouvé.")
        return

    # Charger les prompts
    print("\n✓ Chargement des prompts...")
    try:
        prompts = charger_tous_les_prompts()
        print("  - resume_faits.md")
        print("  - resume_moyens.md")
        print("  - resume_pretentions.md")
    except FileNotFoundError as e:
        print(f"✗ Erreur : {e}")
        return

    print("\n" + "-" * 70)
    print("TEST 1 : Résumé avec méthode HYBRIDE + traitement parallèle")
    print("-" * 70)

    resultat_parallele = resumer_conclusions_parallele(texte_conclusions, prompts, utiliser_hybride=True)

    # Sauvegarder le résultat
    with open("resultat_resume_parallele.md", 'w', encoding='utf-8') as f:
        f.write(resultat_parallele['resume_final'])

    print(f"\n✓ Résumé sauvegardé dans : resultat_resume_parallele.md")
    print(f"  Méthode de découpage : {resultat_parallele['methode_decoupage']}")
    print(f"  Temps total : {resultat_parallele['temps']['total']:.2f}s")

    print("\n" + "=" * 70)
    print("   FIN DU TEST")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
