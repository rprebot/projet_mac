import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Charger les données enrichies (avec colonne Dossier)
df = pd.read_csv('../data/Notation assistant_Submissions_2026-02-09_enrichi.csv')


# =============================================================================
# FONCTIONS POUR POST-STRATIFICATION ET BOOTSTRAP
# =============================================================================

def moyenne_post_stratifiee(data, modele_col, prompt_col, critere_col):
    """
    Calcule la moyenne post-stratifiée pour chaque modèle.
    Chaque prompt (strate) a un poids égal dans le calcul final.
    """
    # Moyenne par (modèle, prompt)
    moyennes_strates = data.groupby([modele_col, prompt_col])[critere_col].mean()

    # Moyenne des moyennes par modèle (post-stratification)
    moyennes_post_strat = moyennes_strates.groupby(level=0).mean()

    return moyennes_post_strat


def bootstrap_post_stratification(data, modele_col, strat_cols, critere_col,
                                   n_bootstrap=1000, ci_level=0.95, seed=42):
    """
    Calcule les intervalles de confiance par bootstrap pour les moyennes post-stratifiées.

    Args:
        data: DataFrame
        modele_col: Colonne du modèle
        strat_cols: Colonne(s) de stratification (str ou list)
        critere_col: Colonne du critère à moyenner
        n_bootstrap: Nombre d'itérations bootstrap
        ci_level: Niveau de confiance
        seed: Graine aléatoire

    Retourne:
        - moyennes: dict {modele: moyenne_post_stratifiée}
        - ci_lower: dict {modele: borne_inférieure_IC}
        - ci_upper: dict {modele: borne_supérieure_IC}
    """
    np.random.seed(seed)

    # Normaliser strat_cols en liste
    if isinstance(strat_cols, str):
        strat_cols = [strat_cols]

    modeles = data[modele_col].unique()

    # Stocker les résultats bootstrap
    bootstrap_results = {modele: [] for modele in modeles}

    for _ in range(n_bootstrap):
        # Rééchantillonnage avec remplacement
        sample = data.sample(n=len(data), replace=True)

        # Calculer moyennes post-stratifiées pour cet échantillon
        for modele in modeles:
            data_modele = sample[sample[modele_col] == modele]
            if len(data_modele) > 0:
                # Moyenne par strate (combinaison des colonnes de stratification)
                moyennes_par_strate = data_modele.groupby(strat_cols)[critere_col].mean()
                # Moyenne des moyennes (post-stratification)
                moyenne_ps = moyennes_par_strate.mean()
                if not np.isnan(moyenne_ps):
                    bootstrap_results[modele].append(moyenne_ps)

    # Calculer les statistiques
    alpha = 1 - ci_level
    moyennes = {}
    ci_lower = {}
    ci_upper = {}

    for modele in modeles:
        if len(bootstrap_results[modele]) > 0:
            arr = np.array(bootstrap_results[modele])
            moyennes[modele] = np.mean(arr)
            ci_lower[modele] = np.percentile(arr, 100 * alpha / 2)
            ci_upper[modele] = np.percentile(arr, 100 * (1 - alpha / 2))
        else:
            moyennes[modele] = np.nan
            ci_lower[modele] = np.nan
            ci_upper[modele] = np.nan

    return moyennes, ci_lower, ci_upper


def bootstrap_multi_criteres(data, modele_col, strat_cols, criteres,
                              n_bootstrap=1000, ci_level=0.95, seed=42):
    """
    Bootstrap pour plusieurs critères à la fois.

    Args:
        strat_cols: Colonne(s) de stratification (str ou list)

    Retourne un dict avec moyennes et IC pour chaque critère.
    """
    results = {}

    for critere in criteres:
        # Filtrer les données non-NA pour ce critère
        data_critere = data.dropna(subset=[critere])

        moyennes, ci_lower, ci_upper = bootstrap_post_stratification(
            data_critere, modele_col, strat_cols, critere,
            n_bootstrap=n_bootstrap, ci_level=ci_level, seed=seed
        )

        results[critere] = {
            'moyennes': moyennes,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        }

    return results

# Renommer les colonnes pour simplifier
df = df.rename(columns={
    'Clarté /  Est-ce que la structure est satisfaisante ? ': 'Clarté',
    'Précision / Est-ce que tous les éléments reportés sont exacts ? ': 'Précision',
    'Fidélité / Est-ce que le résumé est fidèle au(x) document(s) source(s) ? ': 'Fidélité',
    'Intelligibilité de la réponse en langage juridique': 'Intelligibilité',
    'LLMmodel': 'Modèle',
    'Prompt': 'Type_Prompt'
})

# Nettoyer les noms de modèles pour l'affichage
df['Modèle_court'] = df['Modèle'].replace({
    'Albert Large': 'Albert Large',
    'Mixtral 8x22B (Mistral)': 'Mixtral 8x22B',
    'Mistral-medium-2508 (modèle assistant numérique)': 'Mistral-medium',
    'Mistral-medium-2508': 'Mistral-medium',
    'GPT-OSS-120B (Nebius)': 'GPT-OSS-120B',
    'Llama 3.3 70B (Nebius)': 'Llama 3.3 70B'
})

# Nettoyer les noms de prompts pour l'affichage
df['Prompt_court'] = df['Type_Prompt'].replace({
    'Synthèse Rapport': 'Synthèse Rapport',
    'Résumé Conclusions': 'Résumé Conclusions',
    'Résumé Parallèle (faits+moyens+prétentions)': 'Résumé Parallèle',
    'Synthèse Faits & Procédure': 'Faits & Procédure',
    'Synthèse Faits, Procédure & Moyens': 'Faits, Proc. & Moyens',
    'Prompt personnalisable': 'Personnalisable'
})

# Configuration du style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10

# Critères et couleurs globaux
criteres = ['Clarté', 'Précision', 'Fidélité', 'Intelligibilité']
colors = {'Clarté': '#3498db', 'Précision': '#2ecc71', 'Fidélité': '#e74c3c', 'Intelligibilité': '#9b59b6'}
n_bootstrap = 1000

# =============================================================================
# FONCTION POUR GÉNÉRER LE GRAPHIQUE DES MOYENNES
# =============================================================================
def generer_graphique_moyennes(data, output_file, titre_suffix="", n_bootstrap=1000, strat_cols='Prompt_court'):
    """
    Génère le graphique des moyennes post-stratifiées avec IC bootstrap.

    Args:
        data: DataFrame avec les données
        output_file: Nom du fichier de sortie
        titre_suffix: Texte à ajouter au titre
        n_bootstrap: Nombre d'itérations bootstrap
        strat_cols: Colonne(s) de stratification (str ou list)
    """
    criteres = ['Clarté', 'Précision', 'Fidélité', 'Intelligibilité']
    colors = {'Clarté': '#3498db', 'Précision': '#2ecc71', 'Fidélité': '#e74c3c', 'Intelligibilité': '#9b59b6'}

    # Calculer les résultats bootstrap pour tous les critères
    results_bootstrap = bootstrap_multi_criteres(
        data, 'Modèle_court', strat_cols, criteres,
        n_bootstrap=n_bootstrap, ci_level=0.95, seed=42
    )

    # Préparer les données pour le graphique
    modeles = list(results_bootstrap['Clarté']['moyennes'].keys())

    # Trier par moyenne de Clarté (décroissant)
    modeles_sorted = sorted(modeles,
                            key=lambda m: results_bootstrap['Clarté']['moyennes'].get(m, 0),
                            reverse=True)

    # Calculer le nombre d'observations par modèle
    n_obs_par_modele = data.groupby('Modèle_court').size().to_dict()

    fig, ax = plt.subplots(figsize=(12, 7))

    x = np.arange(len(modeles_sorted))
    width = 0.18

    for i, critere in enumerate(criteres):
        offset = (i - 1.5) * width
        moyennes_critere = [results_bootstrap[critere]['moyennes'].get(m, np.nan) for m in modeles_sorted]

        bars = ax.bar(x + offset, moyennes_critere, width,
                       label=critere, color=colors[critere])

        # Ajouter les valeurs sur les barres
        for j, bar in enumerate(bars):
            height = bar.get_height()
            if not np.isnan(height):
                ax.annotate(f'{height:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height + 0.05),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=7)

    ax.set_xlabel('Modèle LLM')
    ax.set_ylabel('Note moyenne post-stratifiée (0-5)')

    titre = 'Moyennes POST-STRATIFIÉES'
    if titre_suffix:
        titre += f'\n{titre_suffix}'
    ax.set_title(titre)

    # Créer les labels avec le nombre d'observations
    labels_avec_n = [f'{m}\n(n={n_obs_par_modele.get(m, 0)})' for m in modeles_sorted]
    ax.set_xticks(x)
    ax.set_xticklabels(labels_avec_n, rotation=0, ha='center')
    ax.legend(loc='upper right')
    ax.set_ylim(0, 5.5)

    # Ajouter une note explicative
    ax.text(0.02, 0.98, f'n = nombre d\'évaluations par modèle',
             transform=ax.transAxes, fontsize=8, verticalalignment='top',
             style='italic', color='gray')

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    return results_bootstrap, modeles_sorted


# =============================================================================
# GRAPHIQUE 1 : Moyennes sur TOUTES les données
# =============================================================================
print("Calcul des moyennes post-stratifiées avec bootstrap (1000 itérations)...")
print(f"  - Données complètes: {len(df)} lignes")

criteres = ['Clarté', 'Précision', 'Fidélité', 'Intelligibilité']
n_bootstrap = 1000

results_bootstrap, modeles_sorted = generer_graphique_moyennes(
    df,
    '../output/graphique_moyennes_llm.png',
    titre_suffix='(Toutes les données - correction biais distribution prompts)',
    n_bootstrap=n_bootstrap
)

print("✓ Graphique 1 sauvegardé : ../output/graphique_moyennes_llm.png")

# =============================================================================
# GRAPHIQUE 1 SMALL PROMPT : Moyennes (sans dossiers 5 et 6, mais avec tests sans dossier)
# =============================================================================
# Filtrer: Exclure seulement les dossiers 5 et 6 (garder les tests sans dossier)
df_small = df[~df['Dossier'].isin([5, 6])].copy()

print(f"\n  - Données filtrées (sans dossiers 5 et 6, tests sans dossier inclus): {len(df_small)} lignes")
dossiers_inclus = df_small['Dossier'].dropna().unique()
n_sans_dossier = df_small['Dossier'].isna().sum()
print(f"    Dossiers inclus: {sorted(dossiers_inclus)} + {n_sans_dossier} tests sans dossier")

if len(df_small) > 0:
    generer_graphique_moyennes(
        df_small,
        '../output/graphique_moyennes_llm_small_prompt.png',
        titre_suffix='(Sans dossiers 5 et 6 - Post-stratification par Prompt)',
        n_bootstrap=n_bootstrap,
        strat_cols='Prompt_court'  # Stratification par prompt uniquement
    )
    print("✓ Graphique 1 small prompt sauvegardé : ../output/graphique_moyennes_llm_small_prompt.png")
else:
    print("⚠ Pas assez de données filtrées pour générer le graphique small prompt")

print("\n✅ Graphiques générés avec succès !")
