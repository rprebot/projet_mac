"""
Module de compression standard (par paquets) pour les conclusions juridiques.

Ce module implémente un pipeline de compression par paquets :
1. Parsing du document en sections
2. Packetisation (découpage en paquets de ~42k tokens)
3. Extraction JSON pour chaque paquet (en parallèle)
4. Génération du résumé final à partir des JSON

Ce mode est adapté aux documents très longs (> 150k tokens).
"""

from .orchestrator import run_standard_compression_pipeline

__all__ = ['run_standard_compression_pipeline']
