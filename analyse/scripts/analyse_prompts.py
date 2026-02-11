import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Charger les données enrichies
df = pd.read_csv('../data/Notation assistant_Submissions_2026-02-09_enrichi.csv')

# =============================================================================
# FONCTIONS POUR POST-STRATIFICATION ET BOOTSTRAP
# =============================================================================

def bootstrap_post_stratification_prompts(data, prompt_col, modele_col, critere_col,
                                          n_bootstrap=1000, ci_level=0.95, seed=42):
    """
    Calcule les intervalles de confiance par bootstrap pour les moyennes post-stratifiées
    des PROMPTS (rééquilibrées par modèle LLM).

    Chaque modèle a un poids égal dans le calcul final pour chaque prompt.
    """
    np.random.seed(seed)

    prompts = data[prompt_col].unique()

    # Stocker les résultats bootstrap
    bootstrap_results = {prompt: [] for prompt in prompts}

    for _ in range(n_bootstrap):
        # Rééchantillonnage avec remplacement
        sample = data.sample(n=len(data), replace=True)

        # Calculer moyennes post-stratifiées pour cet échantillon
        for prompt in prompts:
            data_prompt = sample[sample[prompt_col] == prompt]
            if len(data_prompt) > 0:
                # Moyenne par modèle (strate)
                moyennes_par_modele = data_prompt.groupby(modele_col)[critere_col].mean()
                # Moyenne des moyennes (post-stratification par modèle)
                moyenne_ps = moyennes_par_modele.mean()
                if not np.isnan(moyenne_ps):
                    bootstrap_results[prompt].append(moyenne_ps)

    # Calculer les statistiques
    alpha = 1 - ci_level
    moyennes = {}
    ci_lower = {}
    ci_upper = {}

    for prompt in prompts:
        if len(bootstrap_results[prompt]) > 0:
            arr = np.array(bootstrap_results[prompt])
            moyennes[prompt] = np.mean(arr)
            ci_lower[prompt] = np.percentile(arr, 100 * alpha / 2)
            ci_upper[prompt] = np.percentile(arr, 100 * (1 - alpha / 2))
        else:
            moyennes[prompt] = np.nan
            ci_lower[prompt] = np.nan
            ci_upper[prompt] = np.nan

    return moyennes, ci_lower, ci_upper


def bootstrap_multi_criteres_prompts(data, prompt_col, modele_col, criteres,
                                     n_bootstrap=1000, ci_level=0.95, seed=42):
    """
    Bootstrap pour plusieurs critères à la fois, pour l'analyse des prompts.
    """
    results = {}

    for critere in criteres:
        # Filtrer les données non-NA pour ce critère
        data_critere = data.dropna(subset=[critere])

        moyennes, ci_lower, ci_upper = bootstrap_post_stratification_prompts(
            data_critere, prompt_col, modele_col, critere,
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

# Nettoyer les noms de modèles
df['Modèle_court'] = df['Modèle'].replace({
    'Albert Large': 'Albert Large',
    'Mixtral 8x22B (Mistral)': 'Mixtral 8x22B',
    'Mistral-medium-2508 (modèle assistant numérique)': 'Mistral-medium',
    'Mistral-medium-2508': 'Mistral-medium',
    'GPT-OSS-120B (Nebius)': 'GPT-OSS-120B',
    'Llama 3.3 70B (Nebius)': 'Llama 3.3 70B'
})

# Nettoyer les noms de prompts
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

# Critères et couleurs
criteres = ['Clarté', 'Précision', 'Fidélité', 'Intelligibilité']
colors = {'Clarté': '#3498db', 'Précision': '#2ecc71', 'Fidélité': '#e74c3c', 'Intelligibilité': '#9b59b6'}
n_bootstrap = 1000

# =============================================================================
# GRAPHIQUE : Comparaison des PROMPTS (rééquilibré par modèle)
# =============================================================================
print("=" * 70)
print("COMPARAISON DES PROMPTS (avec rééquilibrage par modèle LLM)")
print("=" * 70)
print(f"\nCalcul des moyennes post-stratifiées avec bootstrap ({n_bootstrap} itérations)...")
print(f"Données initiales: {len(df)} lignes")

# Distribution des données par prompt et modèle
print("\n--- Distribution Prompt x Modèle (avant filtrage) ---")
pivot = pd.crosstab(df['Prompt_court'], df['Modèle_court'])
print(pivot)

# FILTRAGE : Garder seulement les prompts avec plus de 3 observations
prompt_counts = df['Prompt_court'].value_counts()
prompts_valides = prompt_counts[prompt_counts > 3].index.tolist()
df_filtered = df[df['Prompt_court'].isin(prompts_valides)].copy()

print(f"\n--- Filtrage : prompts avec > 3 observations ---")
print(f"Prompts exclus: {[p for p in prompt_counts.index if p not in prompts_valides]}")
print(f"Données après filtrage: {len(df_filtered)} lignes")

# Calculer les résultats bootstrap sur les données filtrées
results_bootstrap = bootstrap_multi_criteres_prompts(
    df_filtered, 'Prompt_court', 'Modèle_court', criteres,
    n_bootstrap=n_bootstrap, ci_level=0.95, seed=42
)

# Préparer les données pour le graphique
# Utiliser TOUS les prompts qui ont au moins une donnée sur n'importe quel critère
all_prompts = set()
for critere in criteres:
    all_prompts.update(results_bootstrap[critere]['moyennes'].keys())
prompts = list(all_prompts)

# Trier par moyenne globale décroissante
def moyenne_globale(p):
    return np.nanmean([results_bootstrap[c]['moyennes'].get(p, np.nan) for c in criteres])

prompts_sorted = sorted(prompts, key=moyenne_globale, reverse=True)

# Nombre d'observations par prompt (sur données filtrées)
n_obs_par_prompt = df_filtered.groupby('Prompt_court').size().to_dict()

# Nombre de modèles distincts par prompt
n_modeles_par_prompt = df_filtered.groupby('Prompt_court')['Modèle_court'].nunique().to_dict()

# Créer le graphique
fig, ax = plt.subplots(figsize=(14, 8))

x = np.arange(len(prompts_sorted))
width = 0.18

for i, critere in enumerate(criteres):
    offset = (i - 1.5) * width
    moyennes_critere = [results_bootstrap[critere]['moyennes'].get(p, np.nan) for p in prompts_sorted]
    ci_lower = [results_bootstrap[critere]['ci_lower'].get(p, np.nan) for p in prompts_sorted]
    ci_upper = [results_bootstrap[critere]['ci_upper'].get(p, np.nan) for p in prompts_sorted]

    # Calculer les erreurs pour les barres d'erreur
    yerr_lower = [m - l if not (np.isnan(m) or np.isnan(l)) else 0 for m, l in zip(moyennes_critere, ci_lower)]
    yerr_upper = [u - m if not (np.isnan(m) or np.isnan(u)) else 0 for m, u in zip(moyennes_critere, ci_upper)]

    bars = ax.bar(x + offset, moyennes_critere, width,
                   label=critere, color=colors[critere], alpha=0.85)

    # Ajouter les barres d'erreur (IC 95%)
    ax.errorbar(x + offset, moyennes_critere, yerr=[yerr_lower, yerr_upper],
                fmt='none', ecolor='black', capsize=2, capthick=1, linewidth=1, alpha=0.7)

    # Ajouter les valeurs sur les barres
    for j, bar in enumerate(bars):
        height = bar.get_height()
        if not np.isnan(height):
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height + 0.08),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, fontweight='bold')

ax.set_xlabel('Type de Prompt', fontsize=11)
ax.set_ylabel('Note moyenne post-stratifiée (0-5)', fontsize=11)
ax.set_title('Comparaison des PROMPTS par critère\n(Moyennes post-stratifiées par modèle LLM - IC 95%)', fontsize=13)

# Labels avec nombre d'observations et de modèles
labels_avec_n = [f'{p}\n(n={n_obs_par_prompt.get(p, 0)}, {n_modeles_par_prompt.get(p, 0)} modèles)'
                 for p in prompts_sorted]
ax.set_xticks(x)
ax.set_xticklabels(labels_avec_n, rotation=15, ha='right', fontsize=9)
ax.legend(loc='upper right', fontsize=10)
ax.set_ylim(0, 5.8)

# Note explicative
ax.text(0.02, 0.98,
        'Post-stratification: chaque modèle LLM a le même poids\n'
        'IC 95% calculé par bootstrap (1000 itérations)',
        transform=ax.transAxes, fontsize=8, verticalalignment='top',
        style='italic', color='gray', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig('../output/graphique_comparaison_prompts.png', dpi=150, bbox_inches='tight')
plt.close()

print("\n--- Résultats par Prompt (triés par moyenne globale) ---")
print("-" * 70)

for prompt in prompts_sorted:
    print(f"\n{prompt}:")
    print(f"  Observations: {n_obs_par_prompt.get(prompt, 0)}, Modèles testés: {n_modeles_par_prompt.get(prompt, 0)}")
    for critere in criteres:
        moy = results_bootstrap[critere]['moyennes'].get(prompt, np.nan)
        ci_l = results_bootstrap[critere]['ci_lower'].get(prompt, np.nan)
        ci_u = results_bootstrap[critere]['ci_upper'].get(prompt, np.nan)
        print(f"  {critere:15}: {moy:.2f} [IC 95%: {ci_l:.2f} - {ci_u:.2f}]")

print("\n" + "=" * 70)
print("Graphique sauvegardé : ../output/graphique_comparaison_prompts.png")
print("=" * 70)

# =============================================================================
# TABLEAU RÉCAPITULATIF
# =============================================================================
print("\n\n" + "=" * 70)
print("TABLEAU RÉCAPITULATIF - Moyennes post-stratifiées par Prompt")
print("=" * 70)

# Créer un DataFrame récapitulatif
recap_data = []
for prompt in prompts_sorted:
    row = {'Prompt': prompt, 'N obs': n_obs_par_prompt.get(prompt, 0),
           'N modèles': n_modeles_par_prompt.get(prompt, 0)}
    for critere in criteres:
        row[critere] = results_bootstrap[critere]['moyennes'].get(prompt, np.nan)
    row['Moyenne globale'] = np.nanmean([row[c] for c in criteres])
    recap_data.append(row)

df_recap = pd.DataFrame(recap_data)
print(df_recap.to_string(index=False, float_format='%.2f'))

# Sauvegarder en CSV
df_recap.to_csv('../data/comparaison_prompts_resultats.csv', index=False, float_format='%.3f')
print("\nTableau sauvegardé : ../data/comparaison_prompts_resultats.csv")

# =============================================================================
# ANALYSE DÉTAILLÉE PAR MODÈLE
# =============================================================================
print("\n\n" + "=" * 70)
print("DÉTAIL : Performance de chaque PROMPT par MODÈLE")
print("=" * 70)

# Pour chaque critère, montrer le tableau croisé Prompt x Modèle (données filtrées)
for critere in criteres:
    print(f"\n--- {critere} ---")
    df_critere = df_filtered.dropna(subset=[critere])
    pivot_critere = df_critere.pivot_table(values=critere, index='Prompt_court',
                                           columns='Modèle_court', aggfunc='mean')
    pivot_critere['Moyenne PS'] = pivot_critere.mean(axis=1)  # Post-stratifiée
    print(pivot_critere.round(2).to_string())

print("\n" + "=" * 70)
print("Analyse terminée avec succès !")
print("=" * 70)
