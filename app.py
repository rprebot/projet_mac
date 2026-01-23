import streamlit as st
import os
import json
from urllib.parse import urlencode
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
    "Résumé Conclusions": "prompts/resume_conclusions.md",
    "Synthèse Faits & Procédure": "prompts/synthese_faits_procedure.md",
    "Synthèse Faits, Procédure & Moyens": "prompts/synthese_faits_procedure_moyens.md",
    "Synthèse Moyens": "prompts/synthese_moyens.md"
}

# Charger les prompts système depuis les fichiers .md
def load_system_prompts():
    """
    Charge les prompts système depuis les fichiers markdown
    """
    prompts = {}

    # Chemins des fichiers de prompts (ordre préservé avec Python 3.7+)
    prompt_files = [
        ("Résumé Conclusions", "prompts/resume_conclusions.md"),
        ("Synthèse Faits & Procédure", "prompts/synthese_faits_procedure.md"),
        ("Synthèse Faits, Procédure & Moyens", "prompts/synthese_faits_procedure_moyens.md"),
        ("Synthèse Moyens", "prompts/synthese_moyens.md")
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
        "Dossier 4 - Conclusion Appelante": "dossiers/Dossier_4_conclusion_appelante.txt",
        "Dossier 4 - Conclusion Intimée": "dossiers/Dossier_4_conclusion_intimee.txt",
        "Dossier 6 - Conclusion Appelant": "dossiers/Dossier_6_conclusion_appelant.txt",
        "Dossier 6 - Conclusion Intimée": "dossiers/Dossier_6_conclusion_intimee.txt",
        "Dossier 8 - Demandeur": "dossiers/Dossier_8_demandeur.txt",
        "Dossier 8 - Intimée": "dossiers/Dossier_8_intimee.txt",
        "Dossier 15 - Défendeur": "dossiers/Dossier_15_defendeur.txt",
        "Dossier 15 - Demandeur": "dossiers/Dossier_15_demandeur.txt"
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

if "evaluations" not in st.session_state:
    st.session_state.evaluations = {}  # Clé = index du message assistant


# Clés API depuis les variables d'environnement
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
ALBERT_API_KEY = os.getenv("ALBERT_API_KEY", "")

# Limites de tokens par modèle (contexte d'entrée)
MODEL_TOKEN_LIMITS = {
    "Albert Large": 128000,
    "Mixtral 8x22B (Mistral)": 64000,
    "Mistral-medium-2508 (modèle assistant numérique)": 128000,
    "GPT-OSS-120B (Nebius)": 128000,
    "Llama 3.3 70B (Nebius)": 128000
}

def estimate_tokens(text):
    """
    Estime le nombre de tokens dans un texte.
    Approximation : 1 token ≈ 4 caractères pour le français.
    """
    if not text:
        return 0
    return len(text) // 4

def count_messages_tokens(system_prompt, messages_history):
    """
    Compte le nombre total de tokens dans les messages.
    """
    total = estimate_tokens(system_prompt)
    for msg in messages_history:
        total += estimate_tokens(msg.get("content", ""))
    return total

def load_evaluation_criteria():
    """
    Charge les critères d'évaluation depuis le fichier evaluation_criteria.json
    """
    try:
        with open("evaluation_criteria.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Charger les critères d'évaluation
EVALUATION_CRITERIA = load_evaluation_criteria()

def load_evaluation_prompt():
    """
    Charge le prompt d'évaluation depuis le fichier evaluation_prompt.md
    """
    try:
        with open("prompts/evaluation_prompt.md", 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None

def evaluate_with_magistral(document_source, reponse_llm, prompt_type):
    """
    Évalue la réponse du LLM avec Magistral Medium (modèle de raisonnement).
    Retourne un dictionnaire avec les scores et le raisonnement.
    """
    if not MISTRAL_API_KEY:
        return {"error": "Clé API Mistral non configurée"}

    # Charger le template du prompt
    prompt_template = load_evaluation_prompt()
    if not prompt_template:
        return {"error": "Fichier evaluation_prompt.md non trouvé"}

    criteria = EVALUATION_CRITERIA.get(prompt_type, EVALUATION_CRITERIA["Résumé Conclusions"])

    # Construire la liste des critères pour le prompt
    criteres_text = "\n".join([f"- **{nom}** : {description}" for nom, description in criteria["criteres"]])
    criteres_json = ", ".join([f'"{nom}": <note 1-5>' for nom, _ in criteria["criteres"]])

    # Formater le prompt avec les variables
    evaluation_prompt = prompt_template.format(
        task_description=criteria["description"],
        document_source=document_source[:15000],
        reponse_llm=reponse_llm,
        criteres_text=criteres_text,
        criteres_json=criteres_json
    )

    try:
        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="magistral-medium-2506",
            messages=[{"role": "user", "content": evaluation_prompt}]
        )

        message = response.choices[0].message
        message_content = message.content

        # Magistral retourne une liste d'objets (ThinkChunk, TextChunk)
        response_text = ""
        reasoning_text = ""

        if isinstance(message_content, list):
            for item in message_content:
                # Accéder aux attributs des objets Mistral
                item_type = getattr(item, 'type', None)

                if item_type == 'thinking':
                    # ThinkChunk contient le raisonnement
                    thinking_content = getattr(item, 'thinking', [])
                    for think_item in thinking_content:
                        if hasattr(think_item, 'text'):
                            reasoning_text += think_item.text

                elif item_type == 'text':
                    # TextChunk contient la réponse finale
                    if hasattr(item, 'text'):
                        response_text += item.text

                # Fallback : essayer d'accéder directement à 'text'
                elif hasattr(item, 'text'):
                    response_text += item.text

        elif isinstance(message_content, str):
            response_text = message_content

        else:
            return {"error": "Format de contenu non reconnu", "raw_response": str(type(message_content))}

        # Si pas de réponse texte, utiliser le raisonnement
        if not response_text and reasoning_text:
            response_text = reasoning_text

        if not response_text:
            return {"error": "Réponse vide de Magistral", "raw_response": str(message_content)}

        # Garder la trace complète (raisonnement + réponse)
        full_response = f"[RAISONNEMENT]\n{reasoning_text}\n\n[RÉPONSE]\n{response_text}"

        # Nettoyer les backticks markdown si présents (```json ... ```)
        import re
        if "```json" in response_text:
            match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if match:
                response_text = match.group(1)
        elif "```" in response_text:
            match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
            if match:
                response_text = match.group(1)

        # Extraire le JSON de la réponse
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                evaluation = json.loads(json_str)
                evaluation["reasoning_trace"] = full_response
                return evaluation
            except json.JSONDecodeError:
                json_str_clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
                evaluation = json.loads(json_str_clean)
                evaluation["reasoning_trace"] = full_response
                return evaluation
        else:
            return {"error": "Format de réponse invalide - Pas de JSON trouvé", "raw_response": response_text}

    except json.JSONDecodeError as e:
        return {"error": f"Erreur parsing JSON: {str(e)}", "raw_response": str(response_text) if 'response_text' in dir() else "N/A"}
    except Exception as e:
        return {"error": f"Erreur évaluation: {str(e)}", "details": str(type(e).__name__)}

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
    ["Albert Large", "Mixtral 8x22B (Mistral)", "Mistral-medium-2508 (modèle assistant numérique)", "GPT-OSS-120B (Nebius)", "Llama 3.3 70B (Nebius)"]
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
        key=f"sidebar_prompt_editor_{prompt_choice}",
        label_visibility="collapsed"
    )
    if st.button("💾 Sauvegarder", use_container_width=True):
        filename = PROMPT_FILES.get(prompt_choice)
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(edited_prompt)
            st.success("✅ Sauvegardé !")
            st.rerun()

# Option d'évaluation automatique
st.sidebar.markdown("---")
st.sidebar.header("Évaluation LLM")
enable_evaluation = st.sidebar.checkbox(
    "Activer l'évaluation Magistral",
    value=False,
    key="enable_magistral_evaluation",
    help="Évalue automatiquement chaque réponse avec Magistral Medium (modèle de raisonnement)"
)

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
        api_url = "https://albert.api.etalab.gouv.fr/v1/chat/completions"
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

    # Mistral Medium 2508 (modèle assistant numérique)
    elif model_choice == "Mistral-medium-2508 (modèle assistant numérique)":
        if not MISTRAL_API_KEY:
            raise ValueError("La clé API Mistral n'est pas configurée.")

        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-medium-2505",
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
    for idx, message in enumerate(st.session_state.messages):
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

        # Afficher le lien vers le formulaire Tally après chaque réponse de l'assistant
        if message["role"] == "assistant":
            # Récupérer la question de l'utilisateur (message précédent)
            user_question = ""
            if idx > 0 and st.session_state.messages[idx - 1]["role"] == "user":
                user_question = st.session_state.messages[idx - 1]["content"]

            # Construire l'URL Tally avec les hidden fields (taille réduite pour éviter les problèmes d'URL)
            tally_params = {
                "Question": user_question[:500],
                "Answer": content[:500],
                "Prompt": prompt_choice,
                "LLMmodel": model_choice
            }
            tally_url = f"https://tally.so/r/9qZx9X?{urlencode(tally_params)}"

            # Lien qui ouvre dans un nouvel onglet
            st.link_button("📝 Donner votre avis sur cette réponse", tally_url, type="secondary")

            # Afficher l'évaluation si disponible
            if idx in st.session_state.evaluations:
                eval_data = st.session_state.evaluations[idx]
                if "error" not in eval_data:
                    with st.expander(f"🎯 Évaluation Magistral - Score global : {eval_data.get('score_global', 'N/A')}/5"):
                        # Scores par critère
                        st.markdown("**Scores par critère :**")
                        scores = eval_data.get("scores", {})
                        raisonnements = eval_data.get("raisonnements", {})

                        for critere, score in scores.items():
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                # Couleur selon le score
                                if score >= 4:
                                    st.success(f"{critere}: {score}/5")
                                elif score >= 3:
                                    st.warning(f"{critere}: {score}/5")
                                else:
                                    st.error(f"{critere}: {score}/5")
                            with col2:
                                st.caption(raisonnements.get(critere, ""))

                        st.markdown("---")

                        # Points forts et améliorations
                        col_forts, col_amelio = st.columns(2)
                        with col_forts:
                            st.markdown("**✅ Points forts :**")
                            for point in eval_data.get("points_forts", []):
                                st.markdown(f"- {point}")
                        with col_amelio:
                            st.markdown("**⚠️ Points à améliorer :**")
                            for point in eval_data.get("points_amelioration", []):
                                st.markdown(f"- {point}")

                        # Synthèse
                        st.markdown("---")
                        st.markdown(f"**Synthèse :** {eval_data.get('synthese', '')}")

                        # Trace de raisonnement (optionnel) - checkbox au lieu d'expander imbriqué
                        if "reasoning_trace" in eval_data:
                            if st.checkbox("🔍 Voir le raisonnement complet", key=f"reasoning_{idx}"):
                                st.code(eval_data["reasoning_trace"], language=None)
                else:
                    st.warning(f"Évaluation échouée : {eval_data.get('error', 'Erreur inconnue')}")
                    # Afficher la réponse brute pour debug - checkbox au lieu d'expander imbriqué
                    if "raw_response" in eval_data:
                        if st.checkbox("🔍 Voir la réponse brute de Magistral", key=f"raw_{idx}"):
                            st.code(str(eval_data["raw_response"]), language=None)

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

        # Vérifier le nombre de tokens avant l'appel
        estimated_tokens = count_messages_tokens(system_prompt, st.session_state.messages)
        token_limit = MODEL_TOKEN_LIMITS.get(model_choice, 32000)

        if estimated_tokens > token_limit:
            st.error(f"""
            ⚠️ **Limite de tokens dépassée**

            - Tokens estimés : **{estimated_tokens:,}** tokens
            - Limite du modèle ({model_choice}) : **{token_limit:,}** tokens
            - Dépassement : **{estimated_tokens - token_limit:,}** tokens

            Veuillez réduire la taille de votre texte ou démarrer une nouvelle conversation.
            """)
            st.session_state.messages.pop()
            st.session_state.message_count -= 1
        else:
            # Afficher info tokens dans la sidebar
            st.sidebar.info(f"📊 Tokens estimés : {estimated_tokens:,} / {token_limit:,}")

            # Générer et afficher la réponse
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

                        # Évaluation automatique si activée
                        if enable_evaluation:
                            with st.spinner("Évaluation avec Magistral Medium..."):
                                # Récupérer le document source (question de l'utilisateur)
                                document_source = user_query
                                eval_result = evaluate_with_magistral(
                                    document_source,
                                    response_text,
                                    prompt_choice
                                )
                                # Stocker l'évaluation avec l'index du message
                                eval_index = len(st.session_state.messages) - 1
                                st.session_state.evaluations[eval_index] = eval_result

                        st.rerun()

                    except Exception as e:
                        error_msg = f"Erreur lors de la génération de la réponse : {str(e)}"
                        st.error(error_msg)
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
