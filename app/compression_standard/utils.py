"""
Fonctions utilitaires pour la compression standard.
"""
import math
import re


def approximate_tokens(text: str) -> int:
    """Approximation simple (1 token pour 4 caractères)."""
    return max(1, math.ceil(len(text) / 4))


def normalize_space(text: str) -> str:
    """Normalise les espaces dans un texte."""
    text = text.replace("\u00A0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_line(line: str) -> str:
    """Nettoie une ligne en unifiant les espaces."""
    return re.sub(r"\s+", " ", line).strip()


def split_lines(text: str) -> list[str]:
    """Découpe un texte en lignes."""
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
