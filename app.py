import streamlit as st
import os
from openai import OpenAI
from mistralai import Mistral
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration de la page
st.set_page_config(page_title="Assistant Juridique LLM", layout="wide")

# Titre de l'application
st.title("Assistant Juridique - Résumé de Conclusions")

# Mapping des noms de prompts vers les fichiers
PROMPT_FILES = {
    "Résumé Conclusions": "resume_conclusions.md",
    "Résumé des Faits": "resume_faits.md",
    "Résumé des Moyens": "resume_moyens.md",
    "Résumé des Prétentions": "resume_pretentions.md"
}

# Charger les prompts système depuis les fichiers .md
def load_system_prompts():
    """
    Charge les prompts système depuis les fichiers markdown
    """
    prompts = {}

    # Chemins des fichiers de prompts (ordre préservé avec Python 3.7+)
    # Résumé Conclusions en première position
    prompt_files = [
        ("Résumé Conclusions", "resume_conclusions.md"),
        ("Résumé des Faits", "resume_faits.md"),
        ("Résumé des Moyens", "resume_moyens.md"),
        ("Résumé des Prétentions", "resume_pretentions.md")
    ]

    # Charger chaque fichier
    for name, filename in prompt_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                prompts[name] = f.read()
        except FileNotFoundError:
            prompts[name] = f"Erreur : Le fichier {filename} n'a pas été trouvé."

    return prompts

# Charger les fichiers de conclusions
def load_conclusion_files():
    """
    Charge les fichiers de conclusions juridiques
    """
    files = {}

    conclusion_files = {
        "Dossier 4 - Conclusion Appelante": "Dossier_4_conclusion_appelante.txt",
        "Dossier 6 - Conclusion Appelant": "Dossier_6_conclusion_appelant.txt"
    }

    for name, filename in conclusion_files.items():
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                files[name] = f.read()
        except FileNotFoundError:
            files[name] = f"Erreur : Le fichier {filename} n'a pas été trouvé."

    return files

# Charger les prompts système
SYSTEM_PROMPTS = load_system_prompts()

# Charger les fichiers de conclusions
CONCLUSION_FILES = load_conclusion_files()

# Initialiser session_state pour l'historique
if "messages" not in st.session_state:
    st.session_state.messages = []

if "message_count" not in st.session_state:
    st.session_state.message_count = 0

# Clés API depuis les variables d'environnement
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
ALBERT_API_KEY = os.getenv("ALBERT_API_KEY", "")

# Sidebar - Bouton Nouvelle conversation en haut
if st.sidebar.button("🔄 Nouvelle conversation", type="primary", use_container_width=True):
    st.session_state.messages = []
    st.session_state.message_count = 0
    st.rerun()

st.sidebar.markdown("---")

# Sidebar - Configuration
st.sidebar.header("Configuration")

# Sélection du modèle
model_choice = st.sidebar.selectbox(
    "Modèle LLM",
    ["Albert Large", "Mixtral 8x22B (Mistral)", "GPT-OSS-120B (Nebius)", "Llama 3.3 70B (Nebius)"]
)

# Sélection du prompt système
prompt_choice = st.sidebar.selectbox(
    "Prompt système",
    list(SYSTEM_PROMPTS.keys())
)

# Récupérer le prompt système sélectionné
system_prompt = SYSTEM_PROMPTS[prompt_choice]

# Éditeur du prompt sélectionné
with st.sidebar.expander("✏️ Éditer le prompt"):
    edited_prompt = st.text_area(
        "Contenu du prompt",
        value=system_prompt,
        height=250,
        key="sidebar_prompt_editor",
        label_visibility="collapsed"
    )
    if st.button("💾 Sauvegarder", use_container_width=True):
        filename = PROMPT_FILES.get(prompt_choice)
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(edited_prompt)
            st.success("✅ Sauvegardé !")
            st.rerun()

# Fonction pour appeler le modèle
def call_model(model_choice, system_prompt, messages_history):
    """
    Appelle le modèle sélectionné avec l'historique des messages
    """
    # Construire les messages avec le système + historique
    full_messages = [{"role": "system", "content": system_prompt}] + messages_history

    # Albert Large
    if model_choice == "Albert Large":
        if not ALBERT_API_KEY:
            raise ValueError("La clé API Albert n'est pas configurée.")

        headers = {
            "Authorization": f"Bearer {ALBERT_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "albert-large",
            "messages": full_messages
        }
        # URL à adapter selon la documentation de l'API Albert
        api_url = "https://api.albert.example/v1/chat/completions"
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    # Mixtral 8x22B via Mistral
    elif model_choice == "Mixtral 8x22B (Mistral)":
        if not MISTRAL_API_KEY:
            raise ValueError("La clé API Mistral n'est pas configurée.")

        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=full_messages
        )
        return response.choices[0].message.content

    # GPT-OSS-120B via Nebius (OpenAI compatible)
    elif model_choice == "GPT-OSS-120B (Nebius)":
        if not NEBIUS_API_KEY:
            raise ValueError("La clé API Nebius n'est pas configurée.")

        client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=NEBIUS_API_KEY
        )
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=full_messages,
            temperature=0.7
        )
        return response.choices[0].message.content

    # Llama 3.3 70B via Nebius (OpenAI compatible)
    elif model_choice == "Llama 3.3 70B (Nebius)":
        if not NEBIUS_API_KEY:
            raise ValueError("La clé API Nebius n'est pas configurée.")

        client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=NEBIUS_API_KEY
        )
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct",
            messages=full_messages,
            temperature=0.7
        )
        return response.choices[0].message.content

# Créer les onglets
tab1, tab2 = st.tabs(["💬 Chat", "📄 Fichiers de conclusions"])

# ============================================================
# ONGLET 1 : CHAT
# ============================================================
with tab1:
    st.header("Chat")

    # Afficher l'historique des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            content = message["content"]

            # Pour les messages utilisateur : tronquer si > 1500 caractères
            if message["role"] == "user" and len(content) > 1500:
                st.markdown(f"*[Query - {len(content):,} caractères]*")
                with st.expander("📄 Voir la query complète"):
                    st.code(content, language=None)
            # Pour les messages assistant : tronquer si > 10000 caractères
            elif message["role"] == "assistant" and len(content) > 10000:
                st.markdown(f"{content[:500]}...\n\n*[Réponse tronquée - {len(content):,} caractères au total]*")
                with st.expander("📄 Voir la réponse complète"):
                    st.markdown(content)
            else:
                st.markdown(content)

    # Zone de saisie - désactivée si on a déjà 5 questions posées
    max_questions = 5
    can_ask = st.session_state.message_count < max_questions

    if not can_ask:
        st.info(f"Limite atteinte : vous avez posé {max_questions} questions (question initiale + 4 relances). Cliquez sur 'Nouvelle conversation' dans la barre latérale pour recommencer.")

    # Zone de saisie de la question
    user_query = st.chat_input(
        "Votre question..." if can_ask else "Limite de questions atteinte",
        disabled=not can_ask
    )

    # Traiter la question de l'utilisateur
    if user_query and can_ask:
        # Ajouter la question de l'utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.session_state.message_count += 1

        # Générer et afficher la réponse (sans afficher la query en temps réel)
        with st.chat_message("assistant"):
            with st.spinner("Génération de la réponse..."):
                try:
                    response_text = call_model(
                        model_choice,
                        system_prompt,
                        st.session_state.messages
                    )

                    # Ajouter la réponse à l'historique
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

                    # Recharger la page pour afficher l'historique complet avec la query repliée
                    st.rerun()

                except Exception as e:
                    error_msg = f"Erreur lors de la génération de la réponse : {str(e)}"
                    st.error(error_msg)
                    # Retirer la dernière question en cas d'erreur
                    st.session_state.messages.pop()
                    st.session_state.message_count -= 1

# ============================================================
# ONGLET 2 : FICHIERS DE CONCLUSIONS
# ============================================================
with tab2:
    st.markdown("Cliquez sur l'icône 📋 en haut à droite de chaque bloc pour copier le contenu.")
    for name, content in CONCLUSION_FILES.items():
        with st.expander(name):
            st.code(content, language=None, line_numbers=False)

# Information sur les clés API dans la sidebar
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ Configuration des clés API"):
    st.write("""
    Pour utiliser cette application, vous devez configurer les clés API suivantes
    dans vos variables d'environnement :

    - `ALBERT_API_KEY` pour Albert Large
    - `MISTRAL_API_KEY` pour Mixtral 8x22B
    - `NEBIUS_API_KEY` pour GPT-OSS-120B et Llama 3.3 70B

    Vous pouvez les définir dans un fichier `.env` à la racine du projet.
    """)
