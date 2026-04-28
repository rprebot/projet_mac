#!/bin/bash
echo "🔄 Test du nouveau prompt de compression..."
echo ""
echo "Sauvegarde de l'ancien résultat..."
mv dossier_6_compresse_reconstruit.txt dossier_6_compresse_reconstruit_OLD.txt 2>/dev/null
mv dossier_6_compression_metadata.json dossier_6_compression_metadata_OLD.json 2>/dev/null

echo "Lancement de la compression avec le nouveau prompt..."
python3 compress_dossier6_complete.py

echo ""
echo "📊 Comparaison des résultats:"
echo ""
echo "ANCIEN résultat:"
jq '.sections_reduites[0] | {titre, tokens_original, tokens_reduit, reduction_pct}' dossier_6_compression_metadata_OLD.json 2>/dev/null || echo "Pas de fichier OLD"
echo ""
echo "NOUVEAU résultat:"
jq '.sections_reduites[0] | {titre, tokens_original, tokens_reduit, reduction_pct}' dossier_6_compression_metadata.json 2>/dev/null || echo "Pas encore de nouveau fichier"
