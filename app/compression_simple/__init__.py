"""
Module de compression simplifiée pour les conclusions juridiques.

Ce module implémente un pipeline de compression en 4 étapes :
1. Identification de la structure du document
2. Réduction ciblée des sous-sections volumineuses (Faits/Procédure)
3. Reconstitution du document
4. Génération du résumé final

La compression est "intelligente" : seules les sections narratives (Faits/Procédure)
sont réduites, les sections juridiques (Moyens/Prétentions) restent intactes.
"""

from .orchestrator import run_simple_compression_pipeline

__all__ = ['run_simple_compression_pipeline']
