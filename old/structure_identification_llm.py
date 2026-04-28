"""
Module d'identification de la structure d'un document juridique.
"""
import json
from mistralai import Mistral
from .utils import load_prompt


def identify_structure(document: str, api_key: str) -> dict:
    """
    Identifie la structure du document (sections et sous-sections) via appel LLM.

    Args:
        document: Texte complet de la conclusion
        api_key: Clé API Mistral

    Returns:
        Dictionnaire structuré avec sections et sous-sections
        {
            "faits": {
                "sous_sections": [
                    {"titre": "...", "contenu": "..."},
                    ...
                ]
            },
            "procedure": {...},
            "moyens": {"contenu": "..."},
            "pretentions": {"contenu": "..."}
        }
    """
    client = Mistral(api_key=api_key)

    # Charger le prompt d'identification
    system_prompt = load_prompt("identification_structure")

    # Appel LLM pour extraction de structure
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": document}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    # Parser la réponse JSON
    structure = json.loads(response.choices[0].message.content)
    return structure
