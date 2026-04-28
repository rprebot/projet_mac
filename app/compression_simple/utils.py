"""
Utilitaires pour la compression simplifiée.
"""
import os
import tiktoken
from pathlib import Path


def estimate_tokens(text: str) -> int:
    """
    Estime le nombre de tokens dans un texte en utilisant tiktoken.

    Args:
        text: Texte à analyser

    Returns:
        Nombre estimé de tokens
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback: approximation 1 token ≈ 4 caractères
        return len(text) // 4


def load_prompt(prompt_name: str) -> str:
    """
    Charge un fichier de prompt depuis le dossier prompts/.

    Args:
        prompt_name: Nom du fichier prompt (sans extension .md)

    Returns:
        Contenu du prompt
    """
    # Remonter au dossier parent (app/) puis aller dans prompts/
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_path = prompts_dir / f"{prompt_name}.md"

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
