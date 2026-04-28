"""
Module de reconstitution du document à partir de la structure.
"""


def reconstruct_document(structure: dict) -> str:
    """
    Reconstruit le document complet à partir de la structure (sections réduites + sections intactes).
    Préserve l'ordre original des sections en utilisant le champ 'position'.

    Args:
        structure: Dictionnaire avec sections et sous-sections

    Returns:
        Document reconstitué sous forme de texte
    """
    # Collecter toutes les sous-sections avec leur position
    all_subsections = []

    for section_name in ["faits", "procedure", "moyens", "pretentions"]:
        if section_name in structure and "sous_sections" in structure[section_name]:
            for subsection in structure[section_name]["sous_sections"]:
                all_subsections.append(subsection)

    # Trier par position pour conserver l'ordre original
    all_subsections.sort(key=lambda x: x.get("position", 999999))

    # Reconstruire dans l'ordre
    parts = []
    for subsection in all_subsections:
        titre = subsection.get("titre", "")
        contenu = subsection.get("contenu", "")

        if titre:
            parts.append(f"{titre}\n")
        parts.append(f"{contenu}\n\n")

    return "\n".join(parts)
