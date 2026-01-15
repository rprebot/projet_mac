# Test de Modèles LLM avec Streamlit

Application Streamlit pour tester et comparer trois modèles LLM :
- Llama 3.3 70B (via Nebius)
- Mixtral 8x22B (via Mistral)
- Albert Large

## Installation

1. Clonez ce repository ou créez un nouveau dossier pour le projet

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurez vos clés API :
```bash
cp .env.example .env
```

4. Éditez le fichier `.env` et ajoutez vos clés API

## Configuration des clés API

### Nebius (Llama 3.3 70B)
Obtenez votre clé API depuis [Nebius Studio](https://studio.nebius.ai/)

### Mistral (Mixtral 8x22B)
Obtenez votre clé API depuis [Mistral AI](https://console.mistral.ai/)

### Albert
Obtenez votre clé API depuis votre fournisseur Albert (adaptez l'URL dans `app.py` selon votre configuration)

## Utilisation

Lancez l'application avec :
```bash
streamlit run app.py
```

L'application s'ouvrira dans votre navigateur par défaut.

## Fonctionnalités

- Sélection du modèle LLM dans la barre latérale
- Configuration du prompt système personnalisé
- Envoi d'une question et réception de la réponse
- Interface simple et intuitive

## Notes

- L'implémentation pour Albert Large est générique et devra être adaptée selon la documentation de votre API Albert
- Les clés API ne sont jamais exposées dans l'interface
- Chaque requête est indépendante (pas de conservation de l'historique de conversation)
