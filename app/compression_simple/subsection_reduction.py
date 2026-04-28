"""
Module de réduction de sous-sections volumineuses.
"""
import time
from mistralai import Mistral
from .utils import load_prompt, estimate_tokens


def reduce_subsection(subsection_content: str, api_key: str, reduction_pct: float = 20.0) -> str:
    """
    Réduit une sous-section de X% via résumé LLM.

    Args:
        subsection_content: Contenu de la sous-section à réduire
        api_key: Clé API Mistral
        reduction_pct: Pourcentage de réduction cible (défaut: 20%)

    Returns:
        Texte résumé de la sous-section
    """
    client = Mistral(api_key=api_key)

    # Charger le prompt de résumé
    system_prompt = load_prompt("resume_subsection")

    # Calculer la taille cible
    original_tokens = estimate_tokens(subsection_content)
    target_tokens = int(original_tokens * (1 - reduction_pct / 100))
    keep_pct = 100 - reduction_pct

    user_message = f"""IMPORTANT : Ce texte fait actuellement {original_tokens:,} tokens. Tu dois le compresser LÉGÈREMENT pour qu'il fasse environ {target_tokens:,} tokens (GARDER {keep_pct:.0f}% du contenu).

Ce n'est PAS un résumé drastique. Tu dois CONSERVER la quasi-totalité du texte en supprimant uniquement les formulations verbeuses.

Texte à compresser :

{subsection_content}

RAPPEL : Ton texte final doit faire environ {target_tokens:,} tokens (soit {keep_pct:.0f}% de {original_tokens:,} tokens)."""

    # Appel LLM pour compression légère (20%) avec retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3
                # Pas de max_tokens pour laisser le modèle atteindre naturellement 80% du texte
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 5 * (2 ** attempt)  # 5s, 10s, 20s
                print(f"      ⚠️  Erreur: {str(e)}")
                print(f"      🔄 Nouvelle tentative dans {wait_time}s... ({attempt + 2}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"      ❌ Échec après {max_retries} tentatives")
                raise
