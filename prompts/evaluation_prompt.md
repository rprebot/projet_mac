Vous êtes un évaluateur juridique expert. Vous devez évaluer la qualité d'une synthèse/résumé juridique produite par un LLM.

## Contexte
Type de tâche : {task_description}

## Document source (extrait des conclusions)
{document_source}

## Réponse du LLM à évaluer
{reponse_llm}

## Critères d'évaluation
{criteres_text}

## Instructions
1. Analyse attentivement le document source et la réponse du LLM
2. Pour chaque critère, attribue une note de 1 à 5 :
   - 1 = Très insuffisant (élément absent ou totalement erroné)
   - 2 = Insuffisant (élément partiellement présent avec erreurs importantes)
   - 3 = Passable (élément présent mais incomplet ou imprécis)
   - 4 = Bien (élément présent et correct avec quelques améliorations possibles)
   - 5 = Excellent (élément parfaitement traité)

3. Fournissez votre raisonnement détaillé pour chaque critère

## Format de réponse (JSON strict)
Réponds UNIQUEMENT avec un JSON valide, sans texte avant ou après :
{{
    "scores": {{
        {criteres_json}
    }},
    "raisonnements": {{
        {criteres_json}
    }},
    "score_global": <moyenne des scores>,
    "points_forts": ["<point fort 1>", "<point fort 2>"],
    "points_amelioration": ["<amélioration 1>", "<amélioration 2>"],
    "synthese": "<synthèse globale de l'évaluation en 2-3 phrases>"
}}
