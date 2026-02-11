"""
Post-traitement du fichier Tally CSV
Ajoute une colonne "Dossier" en identifiant le dossier source à partir du contenu du prompt
"""

import pandas as pd
import os
import re
from pathlib import Path


def charger_fichiers_conclusions(dossier_path='../app/dossiers'):
    """
    Charge tous les fichiers de conclusions et extrait des fragments pour le matching.

    Retourne un dict: {numero_dossier: {'fichiers': [...], 'fragments': [...]}}
    """
    dossiers = {}

    for fichier in Path(dossier_path).glob('*.txt'):
        # Extraire le numéro de dossier du nom du fichier (ex: Dossier_4_... -> 4)
        match = re.search(r'[Dd]ossier_(\d+)', fichier.name)
        if not match:
            continue

        num_dossier = match.group(1)

        # Lire le contenu du fichier
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                contenu = f.read()
        except Exception as e:
            print(f"Erreur lecture {fichier}: {e}")
            continue

        # Initialiser le dossier si pas encore fait
        if num_dossier not in dossiers:
            dossiers[num_dossier] = {'fichiers': [], 'fragments': []}

        dossiers[num_dossier]['fichiers'].append(fichier.name)

        # Extraire plusieurs fragments du fichier pour le matching
        # On prend des fragments à différents endroits du document
        fragments = extraire_fragments(contenu, longueur=100, nb_fragments=10)
        dossiers[num_dossier]['fragments'].extend(fragments)

    return dossiers


def extraire_fragments(texte, longueur=100, nb_fragments=10):
    """
    Extrait plusieurs fragments d'un texte pour servir de signatures.
    PRIORITÉ AU DÉBUT du fichier car le champ Question est tronqué à ~500 chars.
    """
    # Nettoyer le texte
    texte_clean = re.sub(r'\s+', ' ', texte)  # Normaliser les espaces

    fragments = []

    if len(texte_clean) < longueur:
        return [texte_clean] if len(texte_clean) > 20 else []

    # IMPORTANT: Extraire surtout des fragments du DÉBUT (premiers 1000 chars)
    # car le champ Question est tronqué à ~500 caractères

    # Fragments courts du tout début (priorité maximale)
    for start in range(0, min(500, len(texte_clean) - 30), 50):
        for l in [30, 40, 50, 60, 80]:
            if start + l <= len(texte_clean):
                fragment = texte_clean[start:start + l]
                if len(re.sub(r'[^a-zA-ZÀ-ÿ0-9]', '', fragment)) > l * 0.4:
                    fragments.append(fragment)

    # Quelques fragments plus longs du début
    for start in range(0, min(800, len(texte_clean) - longueur), 100):
        fragment = texte_clean[start:start + longueur]
        if len(re.sub(r'[^a-zA-ZÀ-ÿ0-9]', '', fragment)) > longueur * 0.4:
            fragments.append(fragment)

    return fragments


def identifier_dossier(question, dossiers_data, seuil_longueur=25):
    """
    Identifie le dossier correspondant à une question en cherchant des fragments communs.

    Args:
        question: Le texte du champ Question du CSV
        dossiers_data: Les données des dossiers avec leurs fragments
        seuil_longueur: Longueur minimale de la correspondance

    Returns:
        Le numéro de dossier trouvé ou None
    """
    if pd.isna(question) or not question:
        return None

    # Normaliser la question
    question_clean = re.sub(r'\s+', ' ', str(question))

    meilleur_match = None
    meilleure_longueur = 0

    for num_dossier, data in dossiers_data.items():
        for fragment in data['fragments']:
            # Chercher si le fragment est présent dans la question
            if fragment in question_clean:
                if len(fragment) > meilleure_longueur:
                    meilleure_longueur = len(fragment)
                    meilleur_match = num_dossier

    # Si pas de match exact, on n'en a pas trouvé
    # (les fragments sont déjà de différentes tailles)

    return meilleur_match


def post_traiter_csv(input_csv, output_csv=None, dossier_conclusions='dossiers'):
    """
    Ajoute la colonne "Dossier" au fichier CSV de Tally.

    Args:
        input_csv: Chemin vers le fichier CSV d'entrée
        output_csv: Chemin vers le fichier CSV de sortie (par défaut: input avec _enrichi)
        dossier_conclusions: Dossier contenant les fichiers de conclusions
    """
    # Définir le fichier de sortie
    if output_csv is None:
        base = os.path.splitext(input_csv)[0]
        output_csv = f"{base}_enrichi.csv"

    print(f"Chargement des fichiers de conclusions depuis '{dossier_conclusions}'...")
    dossiers_data = charger_fichiers_conclusions(dossier_conclusions)

    print(f"  - {len(dossiers_data)} dossiers trouvés: {list(dossiers_data.keys())}")
    for num, data in dossiers_data.items():
        print(f"    Dossier {num}: {len(data['fragments'])} fragments, fichiers: {data['fichiers']}")

    print(f"\nChargement du CSV '{input_csv}'...")
    df = pd.read_csv(input_csv)
    print(f"  - {len(df)} lignes")

    # Identifier le dossier pour chaque ligne
    print("\nIdentification des dossiers...")
    df['Dossier'] = df['Question'].apply(lambda q: identifier_dossier(q, dossiers_data))

    # Statistiques
    dossiers_trouves = df['Dossier'].notna().sum()
    print(f"\nRésultats:")
    print(f"  - Dossiers identifiés: {dossiers_trouves}/{len(df)} ({100*dossiers_trouves/len(df):.1f}%)")
    print(f"\nDistribution par dossier:")
    print(df['Dossier'].value_counts(dropna=False))

    # Sauvegarder
    df.to_csv(output_csv, index=False)
    print(f"\nFichier enrichi sauvegardé: '{output_csv}'")

    return df


if __name__ == '__main__':
    import sys

    # Par défaut, traiter le fichier le plus récent
    input_file = '../data/Notation assistant_Submissions_2026-02-09.csv'

    if len(sys.argv) > 1:
        input_file = sys.argv[1]

    post_traiter_csv(input_file)
