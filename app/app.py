import streamlit as st
import streamlit.components.v1 as components
import os
import json
import html
import re
from pathlib import Path
from urllib.parse import urlencode
from openai import OpenAI
from mistralai import Mistral
import requests
from dotenv import load_dotenv
import tiktoken
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Répertoire de base (où se trouve app.py)
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent  # Racine du projet (POC_MAC)

# Charger les variables d'environnement depuis .env à la racine du projet
_env_path = PROJECT_ROOT / ".env"
_env_loaded = load_dotenv(_env_path)
print(f"[DEBUG] .env path: {_env_path.absolute()}, exists: {_env_path.exists()}, loaded: {_env_loaded}")

# Import du module de compression pour les documents longs
from document_compression import (
    parse_and_packetize,
    build_extraction_system_prompt,
    build_extraction_user_prompt,
    build_final_system_prompt,
    build_final_user_prompt,
    compute_compressed_tokens,
    approximate_tokens as approx_tokens_simple,
)


def copy_button(text: str, button_id: str):
    """Génère un bouton HTML/JS pour copier du texte dans le presse-papiers (format Word)"""
    # Échapper le texte pour JavaScript
    escaped_text = html.escape(text).replace('\n', '\\n').replace('\r', '').replace("'", "\\'")

    html_code = f"""
    <button id="{button_id}" onclick="copyText_{button_id}()" style="
        background-color: #f0f2f6;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 8px 16px;
        cursor: pointer;
        font-size: 14px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: background-color 0.2s;
    " onmouseover="this.style.backgroundColor='#e0e2e6'" onmouseout="this.style.backgroundColor='#f0f2f6'">
        <span id="icon_{button_id}">📋</span> <span id="label_{button_id}">Copier la réponse</span>
    </button>
    <script>
        function markdownToPlainText(md) {{
            let text = md;
            // Supprimer les blocs de code
            text = text.replace(/```[\\s\\S]*?```/g, function(match) {{
                return match.replace(/```\\w*\\n?/g, '').replace(/```/g, '');
            }});
            // Supprimer le code inline
            text = text.replace(/`([^`]+)`/g, '$1');
            // Convertir les titres (### Titre -> Titre)
            text = text.replace(/^#{1,6}\\s+(.*)$/gm, '$1');
            // Supprimer le gras et italique
            text = text.replace(/\\*\\*\\*(.+?)\\*\\*\\*/g, '$1');
            text = text.replace(/\\*\\*(.+?)\\*\\*/g, '$1');
            text = text.replace(/\\*(.+?)\\*/g, '$1');
            text = text.replace(/___(.+?)___/g, '$1');
            text = text.replace(/__(.+?)__/g, '$1');
            text = text.replace(/_(.+?)_/g, '$1');
            // Convertir les listes à puces en tirets simples
            text = text.replace(/^\\s*[\\*\\-\\+]\\s+/gm, '- ');
            // Convertir les listes numérotées
            text = text.replace(/^\\s*\\d+\\.\\s+/gm, '');
            // Supprimer les liens [texte](url) -> texte
            text = text.replace(/\\[([^\\]]+)\\]\\([^)]+\\)/g, '$1');
            // Supprimer les images
            text = text.replace(/!\\[([^\\]]*)\\]\\([^)]+\\)/g, '$1');
            // Supprimer les lignes horizontales
            text = text.replace(/^[\\-\\*_]{{3,}}$/gm, '');
            // Nettoyer les espaces multiples
            text = text.replace(/  +/g, ' ');
            // Nettoyer les lignes vides multiples
            text = text.replace(/\\n{{3,}}/g, '\\n\\n');
            return text.trim();
        }}

        function copyText_{button_id}() {{
            const text = '{escaped_text}';
            const decodedText = text.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#x27;/g, "'");
            const plainText = markdownToPlainText(decodedText);
            navigator.clipboard.writeText(plainText).then(function() {{
                document.getElementById('icon_{button_id}').innerText = '✅';
                document.getElementById('label_{button_id}').innerText = 'Copié !';
                setTimeout(function() {{
                    document.getElementById('icon_{button_id}').innerText = '📋';
                    document.getElementById('label_{button_id}').innerText = 'Copier la réponse';
                }}, 2000);
            }});
        }}
    </script>
    """
    components.html(html_code, height=50)


# Configuration de la page
st.set_page_config(page_title="Assistant Juridique IA", layout="wide")

# Titre de l'application
st.title("Assistant Juridique IA - Résumé de conclusion et rédaction de l'exposé du litige")

# Mapping des noms de prompts vers les fichiers
PROMPT_FILES = {
    "Résumé Conclusions": BASE_DIR / "prompts/resume_conclusions.md",
    "Synthèse Faits & Procédure": BASE_DIR / "prompts/synthese_faits_procedure.md",
    "Synthèse Moyens": BASE_DIR / "prompts/synthese_moyens.md",
    "Rapport de synthèse": BASE_DIR / "prompts/synthese_faits_procedure_moyens.md",
    "Rédaction Exposé du Litige": BASE_DIR / "prompts/redaction_expose_litige.md"
}


# Charger les prompts système depuis les fichiers .md
def load_system_prompts():
    """
    Charge les prompts système depuis les fichiers markdown
    """
    prompts = {}

    # Chemins des fichiers de prompts (ordre préservé avec Python 3.7+)
    prompt_files = [
        ("Résumé Conclusions", BASE_DIR / "prompts/resume_conclusions.md"),
        ("Synthèse Faits & Procédure", BASE_DIR / "prompts/synthese_faits_procedure.md"),
        ("Synthèse Moyens", BASE_DIR / "prompts/synthese_moyens.md"),
        ("Rapport de synthèse", BASE_DIR / "prompts/synthese_faits_procedure_moyens.md"),
        ("Rédaction Exposé du Litige", BASE_DIR / "prompts/redaction_expose_litige.md")
    ]

    # Charger chaque fichier
    for name, filepath in prompt_files:
        try:
            prompts[name] = filepath.read_text(encoding='utf-8')
        except FileNotFoundError:
            prompts[name] = f"Erreur : Le fichier {filepath} n'a pas été trouvé."

    return prompts

# Charger les fichiers de conclusions
def load_conclusion_files():
    """
    Charge les fichiers de conclusions juridiques
    """
    files = {}

    conclusion_files = {
        "Dossier 4 - Conclusion Appelante": BASE_DIR / "dossiers/Dossier_4_conclusion_appelante.txt",
        "Dossier 4 - Conclusion Intimée": BASE_DIR / "dossiers/Dossier_4_conclusion_intimee.txt",
        "Dossier 5 - Leonard (Employeur)": BASE_DIR / "dossiers/Dossier_5_Leonard_(employeur).txt",
        "Dossier 5 - Leonard (Salarié)": BASE_DIR / "dossiers/Dossier_5_Leonard_(salarie).txt",
        "Dossier 6 - Conclusion Appelant": BASE_DIR / "dossiers/Dossier_6_conclusion_appelant.txt",
        "Dossier 6 - Conclusion Intimée": BASE_DIR / "dossiers/Dossier_6_conclusion_intimee.txt",
        "Dossier 7 - Conclusion Appelante": BASE_DIR / "dossiers/Dossier_7_conculsion_appelante.txt",
        "Dossier 7 - Conclusion Intimée": BASE_DIR / "dossiers/Dossier_7_conclusion_intimee.txt",
        "Dossier 8 - Demandeur": BASE_DIR / "dossiers/Dossier_8_demandeur.txt",
        "Dossier 8 - Intimée": BASE_DIR / "dossiers/Dossier_8_intimee.txt",
        "Dossier 9-2 - Demandeur": BASE_DIR / "dossiers/Dossier_9-2_demandeur.txt",
        "Dossier 9-2 - Défendeur": BASE_DIR / "dossiers/Dossier_9-2_defendeur.txt",
        "Dossier 13 - Conclusion Défendeur": BASE_DIR / "dossiers/dossier_13_conclusion_defendeur.txt",
        "Dossier 14 - Défendeur": BASE_DIR / "dossiers/Doissier 14 - defendeur.txt",
        "Dossier 14 - Demandeur": BASE_DIR / "dossiers/Dossier 14 - demandeur.txt",
        "Dossier 15 - Défendeur": BASE_DIR / "dossiers/Dossier_15_defendeur.txt",
        "Dossier 15 - Demandeur": BASE_DIR / "dossiers/Dossier_15_demandeur.txt",
        "Dossier 17-3 - Assignation": BASE_DIR / "dossiers/Dossier_17-3_Dossier  assignation sans def .txt"
    }

    for name, filepath in conclusion_files.items():
        try:
            files[name] = filepath.read_text(encoding='utf-8')
        except FileNotFoundError:
            files[name] = f"Erreur : Le fichier {filepath} n'a pas été trouvé."

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

if "custom_prompt" not in st.session_state:
    st.session_state.custom_prompt = "Vous êtes un assistant juridique. Répondez aux questions de l'utilisateur de manière précise et professionnelle."

if "custom_trame" not in st.session_state:
    st.session_state.custom_trame = """[TRAME À COMPLÉTER]

Renseignez ici la structure de l'exposé du litige que vous souhaitez obtenir.

Exemple :
## I. EXPOSÉ DU LITIGE
### A. Les faits
[Consignes pour cette section...]

### B. La procédure
[Consignes pour cette section...]

### C. Les prétentions des parties
[Consignes pour cette section...]

### D. Les moyens des parties
[Consignes pour cette section...]
"""

# Clés API depuis les variables d'environnement
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
print(f"[DEBUG] MISTRAL_API_KEY loaded: {bool(MISTRAL_API_KEY)} ({len(MISTRAL_API_KEY)} chars)")
print(f"[DEBUG] NEBIUS_API_KEY loaded: {bool(NEBIUS_API_KEY)} ({len(NEBIUS_API_KEY)} chars)")

# Limites de tokens par modèle (contexte d'entrée)
MODEL_TOKEN_LIMITS = {
    "Mixtral 8x22B (Mistral)": 64000,
    "Mistral-medium-2508": 128000,
    "Mistral Large 2": 131072,
    "Mistral Small 4": 256000,
    "GPT-OSS-120B (Nebius)": 128000,
    "Nemotron Super 120B (Nebius)": 1000000
}

def estimate_tokens(text):
    """
    Compte le nombre de tokens dans un texte en utilisant tiktoken.
    Utilise l'encodage cl100k_base (GPT-4, compatible avec la plupart des LLMs modernes).
    """
    if not text:
        return 0
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

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
        return json.loads((BASE_DIR / "evaluation_criteria.json").read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {}

# Charger les critères d'évaluation
EVALUATION_CRITERIA = load_evaluation_criteria()

def load_evaluation_prompt():
    """
    Charge le prompt d'évaluation depuis le fichier evaluation_prompt.md
    """
    try:
        return (BASE_DIR / "prompts/evaluation_prompt.md").read_text(encoding='utf-8')
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
    ["Mixtral 8x22B (Mistral)", "Mistral-medium-2508", "Mistral Large 2", "Mistral Small 4", "GPT-OSS-120B (Nebius)", "Nemotron Super 120B (Nebius)"]
)

# Sélection du prompt système (5 options uniquement)
prompt_options = [
    "Résumé Conclusions",
    "Résumé Conclusions (mode compression)",
    "Rapport de synthèse",
    "Rapport de synthèse (mode compression)",
    "Prompt personnalisable"
]
prompt_choice = st.sidebar.selectbox(
    "Prompt système",
    prompt_options
)

# Détecter automatiquement si le mode compression est activé
enable_compression = "(mode compression)" in prompt_choice

# Afficher une info si mode compression activé
if enable_compression:
    st.sidebar.info("📦 Mode compression : le document sera découpé en paquets et traité en plusieurs étapes.")

# Mapping des prompts compression vers les fichiers
COMPRESSION_PROMPT_FILES = {
    "Résumé Conclusions (mode compression)": BASE_DIR / "prompts/resume_conclusions_compression_mode.md",
    "Rapport de synthèse (mode compression)": BASE_DIR / "prompts/synthese_faits_procedure_moyens_compression_mode.md",
}

# Mapping des prompts standards vers les clés SYSTEM_PROMPTS
PROMPT_MAPPING = {
    "Résumé Conclusions": "Résumé Conclusions",
    "Rapport de synthèse": "Rapport de synthèse",
}

# Récupérer le prompt système sélectionné
if prompt_choice == "Prompt personnalisable":
    system_prompt = st.session_state.custom_prompt
elif enable_compression:
    # Pour les modes compression, le prompt sera chargé par document_compression.py
    # On stocke juste une référence pour l'affichage
    system_prompt = f"[Mode compression - prompt chargé depuis {COMPRESSION_PROMPT_FILES[prompt_choice].name}]"
else:
    # Pour les prompts standards, utiliser le mapping
    prompt_key = PROMPT_MAPPING.get(prompt_choice, prompt_choice)
    system_prompt = SYSTEM_PROMPTS.get(prompt_key, f"Prompt non trouvé: {prompt_choice}")

# Éditeur du prompt sélectionné (sauf pour le prompt personnalisable qui a son propre onglet)
if prompt_choice != "Prompt personnalisable":
    with st.sidebar.expander("✏️ Éditer le prompt"):
        edited_prompt = st.text_area(
            "Contenu du prompt",
            value=system_prompt,
            height=250,
            key=f"sidebar_prompt_editor_{prompt_choice}",
            label_visibility="collapsed"
        )
        if st.button("💾 Sauvegarder", use_container_width=True):
            filepath = PROMPT_FILES.get(prompt_choice)
            if filepath:
                filepath.write_text(edited_prompt, encoding='utf-8')
                st.success("✅ Sauvegardé !")
                st.rerun()
else:
    st.sidebar.info("✏️ Éditez votre prompt dans l'onglet 'Prompt personnalisable'")

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
    import time
    call_start = time.time()

    # Construire les messages avec le système + historique
    full_messages = [{"role": "system", "content": system_prompt}] + messages_history

    # Calculer les tokens approximatifs
    total_content = system_prompt + "".join([m.get("content", "") for m in messages_history])
    approx_input_tokens = len(total_content) // 4

    print(f"      📡 call_model() appelé", flush=True)
    print(f"         └─ Modèle: {model_choice}", flush=True)
    print(f"         └─ Tokens input estimés: ~{approx_input_tokens:,}", flush=True)

    # Mixtral 8x22B via Mistral
    if model_choice == "Mixtral 8x22B (Mistral)":
        if not MISTRAL_API_KEY:
            raise ValueError("La clé API Mistral n'est pas configurée.")

        print(f"         └─ 🔄 Appel API Mistral (mistral-large-latest)...", flush=True)
        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=full_messages,
            temperature=0.3,
            max_tokens=16000  # Suffisant pour ~10-12 pages
        )
        elapsed = time.time() - call_start
        print(f"         └─ ✅ Réponse reçue en {elapsed:.1f}s", flush=True)
        return response.choices[0].message.content

    # Mistral Medium 2508 (modèle assistant numérique)
    elif model_choice == "Mistral-medium-2508":
        if not MISTRAL_API_KEY:
            raise ValueError("La clé API Mistral n'est pas configurée.")

        print(f"         └─ 🔄 Appel API Mistral (mistral-medium-2508)...", flush=True)
        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-medium-2508",
            messages=full_messages,
            temperature=0.3,
            max_tokens=16000  # Suffisant pour ~10-12 pages
        )
        elapsed = time.time() - call_start
        print(f"         └─ ✅ Réponse reçue en {elapsed:.1f}s", flush=True)
        return response.choices[0].message.content

    # Mistral Large 2 (modèle flagship)
    elif model_choice == "Mistral Large 2":
        if not MISTRAL_API_KEY:
            raise ValueError("La clé API Mistral n'est pas configurée.")

        print(f"         └─ 🔄 Appel API Mistral (mistral-large-2411)...", flush=True)
        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-large-2411",
            messages=full_messages,
            temperature=0.3,
            max_tokens=16000  # Suffisant pour ~10-12 pages
        )
        elapsed = time.time() - call_start
        print(f"         └─ ✅ Réponse reçue en {elapsed:.1f}s", flush=True)
        return response.choices[0].message.content

    # Mistral Small 4 (modèle compact performant)
    elif model_choice == "Mistral Small 4":
        if not MISTRAL_API_KEY:
            raise ValueError("La clé API Mistral n'est pas configurée.")

        # Renforcer l'instruction de style et de complétude pour ce modèle
        style_instruction = """

⚠️ INSTRUCTIONS CRITIQUES :

1. COMPLÉTUDE ABSOLUE :
- Tu dois traiter INTÉGRALEMENT toutes les parties du document source
- Ne t'arrête JAMAIS avant d'avoir couvert tous les moyens et arguments de chaque partie
- Ta réponse doit être EXHAUSTIVE et DÉTAILLÉE (minimum 5000 mots)
- Continue jusqu'à la fin complète de l'analyse, même si la réponse est longue

2. STYLE LITTÉRAIRE :
- Rédige en PROSE LITTÉRAIRE avec des paragraphes fluides et continus
- INTERDIT : les listes à puces, les tirets, les numérotations (sauf pour les prétentions/dispositif)
- OBLIGATOIRE : des phrases complètes reliées par des connecteurs logiques (En effet, Par ailleurs, Toutefois, Dès lors, En outre, De surcroît)
- Le texte doit ressembler à un arrêt de cour d'appel, PAS à des notes ou un plan

⚠️ NE T'ARRÊTE PAS AVANT D'AVOIR TOUT TRAITÉ !
"""
        enhanced_system_prompt = system_prompt + style_instruction

        # Ajouter un rappel des instructions à la fin du dernier message utilisateur
        # (technique de "bookending" pour les longs contextes)
        enhanced_messages = [{"role": "system", "content": enhanced_system_prompt}]
        for i, msg in enumerate(messages_history):
            if i == len(messages_history) - 1 and msg["role"] == "user":
                # Dernier message utilisateur : ajouter rappel à la fin
                rappel = """

---
⚠️ RAPPEL FINAL : Ta réponse doit être EXHAUSTIVE et COMPLÈTE (minimum 5000 mots). Traite TOUS les moyens de TOUTES les parties. Ne t'arrête pas avant d'avoir tout couvert. Rédige en prose littéraire fluide, comme un arrêt de cour d'appel.
"""
                enhanced_messages.append({"role": msg["role"], "content": msg["content"] + rappel})
            else:
                enhanced_messages.append(msg)

        print(f"         └─ 🔄 Appel API Mistral (mistral-small-2603)...", flush=True)
        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-small-2603",
            messages=enhanced_messages,
            temperature=0.3,
            max_tokens=65536  # Augmenté pour éviter la troncature
        )
        elapsed = time.time() - call_start
        # Debug: stocker la raison d'arrêt pour affichage
        finish_reason = response.choices[0].finish_reason
        usage = response.usage
        st.session_state["debug_finish_reason"] = finish_reason
        st.session_state["debug_usage"] = f"Tokens: {usage.prompt_tokens} (prompt) + {usage.completion_tokens} (completion) = {usage.total_tokens} (total)"

        # Log console pour debug supplémentaire
        print(f"         └─ ✅ Réponse reçue en {elapsed:.1f}s (finish_reason={finish_reason}, tokens={usage.completion_tokens})", flush=True)

        return response.choices[0].message.content

    # GPT-OSS-120B via Nebius (OpenAI compatible) avec reasoning
    elif model_choice == "GPT-OSS-120B (Nebius)":
        if not NEBIUS_API_KEY:
            raise ValueError("La clé API Nebius n'est pas configurée.")

        print(f"         └─ 🔄 Appel API Nebius (gpt-oss-120b)...", flush=True)
        client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=NEBIUS_API_KEY
        )
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=full_messages,
            temperature=0.3,
            max_tokens=16000,  # Suffisant pour ~10-12 pages
            extra_body={
                "reasoning": {
                    "effort": "high"
                }
            }
        )
        elapsed = time.time() - call_start
        print(f"         └─ ✅ Réponse reçue en {elapsed:.1f}s", flush=True)
        return response.choices[0].message.content

    # Nemotron Super 120B via Nebius (OpenAI compatible)
    elif model_choice == "Nemotron Super 120B (Nebius)":
        if not NEBIUS_API_KEY:
            raise ValueError("La clé API Nebius n'est pas configurée.")

        print(f"         └─ 🔄 Appel API Nebius (nemotron-3-super-120b)...", flush=True)
        client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=NEBIUS_API_KEY
        )
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b",
            messages=full_messages,
            temperature=0.3,
            max_tokens=16000  # Suffisant pour ~10-12 pages
        )
        elapsed = time.time() - call_start
        print(f"         └─ ✅ Réponse reçue en {elapsed:.1f}s", flush=True)
        return response.choices[0].message.content


def repair_json_with_llm(malformed_json: str, max_length=10000) -> dict:
    """
    Fallback : utilise un petit LLM pour réparer un JSON malformé.

    Args:
        malformed_json: Le JSON malformé à réparer
        max_length: Longueur max du JSON à envoyer (pour limiter les coûts)

    Returns:
        dict: Le JSON réparé et parsé
    """
    if not MISTRAL_API_KEY:
        raise ValueError("Clé API Mistral non configurée pour le fallback JSON repair")

    # Tronquer si trop long
    json_to_repair = malformed_json[:max_length] if len(malformed_json) > max_length else malformed_json

    repair_prompt = f"""Tu es un expert en réparation de JSON malformé.

TÂCHE : Le JSON ci-dessous contient une ou plusieurs erreurs de syntaxe. Répare-le et retourne UNIQUEMENT le JSON corrigé, sans aucun texte avant ou après.

ERREURS COURANTES À CORRIGER :
- Virgules trailing (avant ] ou }})
- Guillemets non échappés dans les chaînes
- Sauts de ligne non échappés
- Accolades/crochets non fermés
- JSON tronqué (fermer proprement les structures ouvertes)

JSON MALFORMÉ :
```
{json_to_repair}
```

RETOURNE UNIQUEMENT LE JSON CORRIGÉ (sans backticks, sans explication) :"""

    try:
        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-small-2603",
            messages=[{"role": "user", "content": repair_prompt}],
            temperature=0.0,
            max_tokens=max_length + 1000  # Un peu plus pour les corrections
        )

        repaired_text = response.choices[0].message.content

        # Extraire le JSON réparé (même logique que extract_json_from_response)
        json_start = repaired_text.find('{')
        json_end = repaired_text.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            json_str = repaired_text[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError("Le LLM n'a pas retourné de JSON valide")

    except Exception as e:
        raise ValueError(f"Échec du fallback LLM repair: {str(e)}")


def extract_json_from_response(response_text: str, debug=False) -> dict:
    """
    Extrait un objet JSON d'une réponse LLM.
    Gère les cas où le JSON est entouré de backticks markdown.
    Applique plusieurs nettoyages pour corriger les erreurs JSON courantes.
    """
    original_length = len(response_text)

    # Stratégie 1 : Chercher le premier { et le dernier } (ignore les backticks)
    # Cette approche est plus robuste que le regex si les backticks sont malformés
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1

    if json_start == -1 or json_end <= json_start:
        raise ValueError("Aucune accolade { } trouvée dans la réponse")

    json_str = response_text[json_start:json_end]

    if debug:
        print(f"[DEBUG extract_json] Original length: {original_length}, JSON extracted: {len(json_str)} chars")
        print(f"[DEBUG extract_json] First 200 chars: {json_str[:200]}")

    # Tentative 1 : Parser tel quel
    try:
        result = json.loads(json_str)
        if debug:
            print(f"[DEBUG extract_json] ✅ Parsed on attempt 1 (as-is)")
        return result
    except json.JSONDecodeError as e:
        if debug:
            print(f"[DEBUG extract_json] ❌ Attempt 1 failed: {str(e)[:100]}")

    # Tentative 2 : Nettoyer les caractères de contrôle (sauf \n, \r, \t légitimes dans les strings)
    try:
        json_str_clean = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        result = json.loads(json_str_clean)
        if debug:
            print(f"[DEBUG extract_json] ✅ Parsed on attempt 2 (remove control chars)")
        return result
    except json.JSONDecodeError as e:
        if debug:
            print(f"[DEBUG extract_json] ❌ Attempt 2 failed: {str(e)[:100]}")

    # Tentative 3 : Nettoyer les virgules trailing (,] et ,})
    try:
        json_str_clean = re.sub(r',\s*([}\]])', r'\1', json_str)
        json_str_clean = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', json_str_clean)
        result = json.loads(json_str_clean)
        if debug:
            print(f"[DEBUG extract_json] ✅ Parsed on attempt 3 (remove trailing commas)")
        return result
    except json.JSONDecodeError as e:
        if debug:
            print(f"[DEBUG extract_json] ❌ Attempt 3 failed: {str(e)[:100]}")

    # Tentative 4 : Remplacer les sauts de ligne non échappés dans les strings
    try:
        # Protéger les vraies nouvelles lignes échappées (\n)
        json_str_clean = json_str.replace('\\n', '__NEWLINE__ESCAPED__')
        json_str_clean = json_str_clean.replace('\\r', '__RETURN__ESCAPED__')
        json_str_clean = json_str_clean.replace('\\t', '__TAB__ESCAPED__')

        # Supprimer les vraies nouvelles lignes/retours (non échappés dans le JSON brut)
        json_str_clean = json_str_clean.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        # Restaurer les échappements
        json_str_clean = json_str_clean.replace('__NEWLINE__ESCAPED__', '\\n')
        json_str_clean = json_str_clean.replace('__RETURN__ESCAPED__', '\\r')
        json_str_clean = json_str_clean.replace('__TAB__ESCAPED__', '\\t')

        # Nettoyer virgules et caractères de contrôle
        json_str_clean = re.sub(r',\s*([}\]])', r'\1', json_str_clean)
        json_str_clean = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', json_str_clean)

        result = json.loads(json_str_clean)
        if debug:
            print(f"[DEBUG extract_json] ✅ Parsed on attempt 4 (replace unescaped newlines)")
        return result
    except json.JSONDecodeError as e:
        if debug:
            print(f"[DEBUG extract_json] ❌ Attempt 4 failed: {str(e)[:100]}")
            # Montrer où se trouve l'erreur
            error_pos = getattr(e, 'pos', None)
            if error_pos:
                context_start = max(0, error_pos - 100)
                context_end = min(len(json_str_clean), error_pos + 100)
                print(f"[DEBUG extract_json] Error context: ...{json_str_clean[context_start:context_end]}...")

    # Tentative 5 : FALLBACK - Utiliser un petit LLM pour réparer le JSON
    try:
        if debug:
            print(f"[DEBUG extract_json] 🤖 Attempt 5: Fallback LLM repair...")
        result = repair_json_with_llm(json_str)
        if debug:
            print(f"[DEBUG extract_json] ✅ Parsed on attempt 5 (LLM repair)")
        return result
    except Exception as e:
        if debug:
            print(f"[DEBUG extract_json] ❌ Attempt 5 failed: {str(e)[:100]}")

        # Toutes les tentatives ont échoué
        raise ValueError(f"Impossible de parser le JSON après tous les nettoyages + LLM repair. Erreur: {str(e)}")


def call_model_fast_extraction(system_prompt, messages_history, timeout_seconds=120):
    """
    Appelle Mistral Small directement pour les extractions JSON.
    Optimisé pour être rapide avec un timeout explicite.

    Args:
        system_prompt: Le prompt système
        messages_history: Liste des messages
        timeout_seconds: Timeout en secondes (défaut: 120s = 2min)

    Returns:
        Le contenu de la réponse
    """
    import time
    import sys

    call_start = time.time()
    print(f"         [EXTRACTION] Entrée dans call_model_fast_extraction()", flush=True)

    if not MISTRAL_API_KEY:
        raise ValueError("La clé API Mistral n'est pas configurée.")

    print(f"         [EXTRACTION] API Key OK, construction messages...", flush=True)
    full_messages = [{"role": "system", "content": system_prompt}] + messages_history
    total_chars = sum(len(m.get("content", "")) for m in full_messages)
    print(f"         [EXTRACTION] Messages construits: {len(full_messages)} messages, {total_chars:,} chars", flush=True)

    # Créer un client Mistral
    print(f"         [EXTRACTION] Création client Mistral...", flush=True)
    client = Mistral(api_key=MISTRAL_API_KEY)
    print(f"         [EXTRACTION] Client créé, appel API...", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()

    try:
        response = client.chat.complete(
            model="mistral-small-2603",  # Modèle rapide pour l'extraction
            messages=full_messages,
            temperature=0.0,  # Température = 0 pour JSON déterministe et valide
            max_tokens=16000  # Augmenté pour éviter la troncature du JSON
        )

        elapsed = time.time() - call_start
        print(f"         └─ ✅ Extraction reçue en {elapsed:.1f}s", flush=True)
        return response.choices[0].message.content

    except Exception as e:
        elapsed = time.time() - call_start
        print(f"         └─ ❌ Erreur après {elapsed:.1f}s: {type(e).__name__}: {str(e)[:200]}", flush=True)
        raise


def extract_packet_parallel(packet, packet_index, extraction_system_prompt, log_fn, max_retries=1):
    """
    Extrait un paquet en appelant l'API Mistral (thread-safe).
    En cas d'erreur de parsing JSON, réessaie une fois avec un prompt plus strict.

    Args:
        packet: Le paquet à extraire
        packet_index: Index du paquet (pour logs et ordre)
        extraction_system_prompt: Le prompt système d'extraction
        log_fn: Fonction de logging (thread-safe)
        max_retries: Nombre de tentatives en cas d'erreur JSON (défaut: 1)

    Returns:
        tuple: (packet_index, packet, extracted_json, error)
    """
    log_fn(f"      └─ 🔄 PAQUET {packet_index+1} - Début extraction...")
    log_fn(f"         └─ Tokens contenu: {packet.total_tokens:,}")

    extraction_user_prompt = build_extraction_user_prompt(packet)
    prompt_tokens = approx_tokens_simple(extraction_user_prompt)
    log_fn(f"         └─ Tokens prompt total: ~{prompt_tokens:,}")

    # Boucle de retry
    last_response = None  # Pour stocker la dernière réponse brute
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                log_fn(f"         └─ 🔁 RETRY {attempt}/{max_retries} - Nouvelle tentative avec prompt strict...")
                # Ajouter un avertissement strict au prompt pour le retry
                strict_warning = """

⚠️ ATTENTION CRITIQUE - RETRY SUITE À ERREUR JSON :
Votre précédente réponse contenait une erreur de syntaxe JSON.
VOUS DEVEZ ABSOLUMENT :
1. Générer un JSON STRICTEMENT VALIDE (pas d'erreur de virgule, de guillemet, de crochet)
2. Vérifier CHAQUE virgule, CHAQUE guillemet, CHAQUE accolade/crochet
3. Ne PAS mettre de virgule après le dernier élément d'un tableau ou objet
4. Échapper correctement les guillemets à l'intérieur des chaînes (utiliser \\\" ou éviter les guillemets)
5. Retourner UNIQUEMENT le JSON, sans texte avant ou après
"""
                retry_prompt = extraction_user_prompt + strict_warning
                messages = [{"role": "user", "content": retry_prompt}]
            else:
                log_fn(f"         └─ 📡 Envoi requête API (Mistral Small)...")
                messages = [{"role": "user", "content": extraction_user_prompt}]

            response = call_model_fast_extraction(extraction_system_prompt, messages)
            last_response = response  # Sauvegarder pour debug

            response_tokens = approx_tokens_simple(response)
            log_fn(f"         └─ 📥 Réponse reçue: ~{response_tokens:,} tokens")

            # Parser le JSON de la réponse (avec debug activé si on est en retry)
            extracted_json = extract_json_from_response(response, debug=(attempt > 0))
            nb_sections_extracted = len(extracted_json.get("sections", []))

            if attempt > 0:
                log_fn(f"         └─ ✅ RETRY RÉUSSI ! JSON parsé: {nb_sections_extracted} sections extraites")
            else:
                log_fn(f"         └─ ✅ JSON parsé: {nb_sections_extracted} sections extraites")

            return (packet_index, packet, extracted_json, None)

        except (json.JSONDecodeError, ValueError) as e:
            error_msg = f"Erreur parsing JSON: {str(e)}"

            if attempt < max_retries:
                log_fn(f"         └─ ⚠️ {error_msg[:80]} - Retry en cours...")
                # Logger un échantillon de la réponse pour debug
                if last_response:
                    # Trouver le début et la fin du JSON
                    json_start = last_response.find('{')
                    json_end = last_response.rfind('}')

                    if json_start != -1 and json_end != -1:
                        # Montrer le début ET la fin
                        sample_start_begin = max(0, json_start - 50)
                        sample_end_begin = min(len(last_response), json_start + 200)
                        sample_begin = last_response[sample_start_begin:sample_end_begin]
                        if sample_start_begin > 0:
                            sample_begin = "..." + sample_begin

                        sample_start_end = max(0, json_end - 200)
                        sample_end_end = min(len(last_response), json_end + 50)
                        sample_end = last_response[sample_start_end:sample_end_end]
                        if sample_end_end < len(last_response):
                            sample_end = sample_end + "..."

                        log_fn(f"         └─ 🔍 Début JSON: {sample_begin}")
                        log_fn(f"         └─ 🔍 Fin JSON: ...{sample_end}")
                        log_fn(f"         └─ 📏 Longueur JSON: {json_end - json_start + 1} chars (total response: {len(last_response)} chars)")
                    else:
                        sample = last_response[:300] + "..." if len(last_response) > 300 else last_response
                        log_fn(f"         └─ 🔍 Échantillon réponse: {sample}")
                continue  # Réessayer
            else:
                log_fn(f"         └─ ❌ {error_msg[:120]} (après {max_retries} retry)")
                # Logger un échantillon plus long pour le dernier échec
                if last_response:
                    # Trouver le début et la fin du JSON
                    json_start = last_response.find('{')
                    json_end = last_response.rfind('}')

                    if json_start != -1 and json_end != -1:
                        # Montrer le début ET la fin
                        sample_start_begin = max(0, json_start - 100)
                        sample_end_begin = min(len(last_response), json_start + 400)
                        sample_begin = last_response[sample_start_begin:sample_end_begin]
                        if sample_start_begin > 0:
                            sample_begin = "..." + sample_begin

                        sample_start_end = max(0, json_end - 400)
                        sample_end_end = min(len(last_response), json_end + 100)
                        sample_end = last_response[sample_start_end:sample_end_end]
                        if sample_end_end < len(last_response):
                            sample_end = sample_end + "..."

                        log_fn(f"         └─ 🔍 DÉBUT JSON:\n{sample_begin}")
                        log_fn(f"         └─ 🔍 FIN JSON:\n...{sample_end}")
                        log_fn(f"         └─ 📏 Longueur: JSON={json_end - json_start + 1} chars, Total={len(last_response)} chars")
                    else:
                        sample = last_response[:500] + "..." if len(last_response) > 500 else last_response
                        log_fn(f"         └─ 🔍 Échantillon réponse brute:\n{sample}")

                # Créer un résultat d'erreur avec la réponse brute tronquée
                error_result = {
                    "packet_id": packet.id,
                    "error": error_msg,
                    "raw_response_sample": last_response[:2000] if last_response else "N/A"
                }
                return (packet_index, packet, error_result, error_msg)

        except Exception as e:
            error_msg = f"Erreur extraction: {str(e)}"
            log_fn(f"         └─ ❌ {error_msg[:120]}")
            error_result = {
                "packet_id": packet.id,
                "error": error_msg,
                "raw_response_sample": last_response[:2000] if last_response else "N/A"
            }
            return (packet_index, packet, error_result, error_msg)

    # Ne devrait jamais arriver ici
    return (packet_index, packet, None, "Erreur inconnue")


def call_model_with_compression(model_choice, user_query, prompt_type="resume_conclusions", progress_callback=None):
    """
    Pipeline de compression pour les documents longs.

    Étapes :
    1. Parser le document en sections
    2. Découper en paquets
    3. Pour chaque paquet, extraire un JSON intermédiaire via LLM
    4. Générer le résumé final à partir des JSON intermédiaires

    Args:
        model_choice: Le modèle LLM à utiliser
        user_query: Le document source (conclusions)
        prompt_type: Type de prompt de synthèse ("resume_conclusions" ou "rapport_synthese")
        progress_callback: Fonction optionnelle pour afficher la progression

    Returns:
        dict avec les clés:
        - "nb_sections": nombre de sections détectées
        - "nb_packets": nombre de paquets créés
        - "extracted_jsons": liste des JSON intermédiaires
        - "final_response": le résumé final
        - "tokens_original": nombre de tokens du document original
        - "tokens_compressed": nombre de tokens après compression
        - "compression_ratio": ratio de compression
    """
    import time
    import sys
    start_time = time.time()

    def log(msg):
        """Log avec timestamp et flush immédiat"""
        elapsed = time.time() - start_time
        print(f"[{elapsed:6.1f}s] {msg}", flush=True)

    print("\n" + "="*60, flush=True)
    log("🚀 PIPELINE DE COMPRESSION - DÉBUT")
    print("="*60, flush=True)
    log(f"📋 Modèle sélectionné: {model_choice}")

    # Calculer les tokens du document original
    tokens_original = approx_tokens_simple(user_query)
    log(f"📄 Document original: {len(user_query):,} caractères, ~{tokens_original:,} tokens")

    # Étape 1 & 2 : Parser et découper en paquets
    log("📊 ÉTAPE 1/3 - Parsing & Packetisation...")
    if progress_callback:
        progress_callback(f"Analyse du document ({tokens_original:,} tokens)...")

    nodes, packets = parse_and_packetize(
        user_query,
        max_input_tokens=42000,  # Même config que le notebook
        prompt_budget_tokens=2500,
        output_budget_tokens=3000,
    )

    nb_sections = len(nodes)
    nb_packets = len(packets)

    log(f"   ✅ Parsing terminé: {nb_sections} sections détectées")
    for node in nodes:
        log(f"      • {node.id}: {node.title[:50]}{'...' if len(node.title) > 50 else ''} ({node.section_type}, ~{node.approx_tokens} tokens)")
    log(f"   ✅ Packetisation: {nb_packets} paquets créés")
    for packet in packets:
        log(f"      • {packet.id}: {packet.total_tokens:,} tokens, sections: {', '.join(packet.titles[:3])}{'...' if len(packet.titles) > 3 else ''}")

    if progress_callback:
        progress_callback(f"Document découpé : {nb_sections} sections, {nb_packets} paquet(s)")

    # Étape 3 : Extraire un JSON intermédiaire pour chaque paquet (EN PARALLÈLE)
    # On utilise Mistral Small pour l'extraction (plus rapide, suffisant pour le JSON)
    log(f"📊 ÉTAPE 2/3 - Extraction LLM ({nb_packets} paquets) - MODE PARALLÈLE (2 workers)")
    log(f"   ℹ️  Modèle d'extraction: Mistral Small (rapide)")
    extraction_system_prompt = build_extraction_system_prompt()

    # Dictionnaire pour conserver l'ordre des paquets
    extracted_jsons_dict = {}
    max_workers = 2  # Traiter 2 paquets simultanément

    # Lock pour les callbacks progress thread-safe
    progress_lock = threading.Lock()

    # Utiliser ThreadPoolExecutor pour traiter les paquets en parallèle
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Soumettre tous les paquets
        future_to_packet = {
            executor.submit(extract_packet_parallel, packet, i, extraction_system_prompt, log): (i, packet)
            for i, packet in enumerate(packets)
        }

        log(f"   🚀 {len(future_to_packet)} paquets soumis pour extraction parallèle")

        # Récupérer les résultats au fur et à mesure
        completed_count = 0
        for future in as_completed(future_to_packet):
            packet_index, packet, extracted_json, error = future.result()
            completed_count += 1

            # Callback progress (thread-safe)
            with progress_lock:
                if progress_callback:
                    progress_callback(f"Extraction : {completed_count}/{nb_packets} paquets traités")

            # Stocker le résultat dans le dictionnaire (avec ou sans erreur)
            if error:
                # Si erreur, extracted_json contient déjà le dict d'erreur avec raw_response_sample
                if isinstance(extracted_json, dict):
                    extracted_jsons_dict[packet_index] = extracted_json
                else:
                    # Fallback si le format n'est pas correct
                    extracted_jsons_dict[packet_index] = {
                        "packet_id": packet.id,
                        "error": f"Erreur: {error}",
                        "raw_response": ""
                    }
            else:
                extracted_jsons_dict[packet_index] = extracted_json

    # Reconstituer la liste dans l'ordre original
    extracted_jsons = [extracted_jsons_dict[i] for i in range(nb_packets)]
    log(f"   ✅ Extraction parallèle terminée: {len(extracted_jsons)} paquets traités")

    # Calculer les tokens du contenu compressé
    tokens_compressed = compute_compressed_tokens(extracted_jsons)
    compression_ratio = round((1 - tokens_compressed / tokens_original) * 100, 1) if tokens_original > 0 else 0

    log(f"📊 RÉSULTAT COMPRESSION INTERMÉDIAIRE")
    log(f"   └─ Tokens original: {tokens_original:,}")
    log(f"   └─ Tokens compressé: {tokens_compressed:,}")
    log(f"   └─ Ratio de compression: {compression_ratio}%")

    if progress_callback:
        progress_callback(f"Compression : {tokens_original:,} → {tokens_compressed:,} tokens ({compression_ratio}% de réduction)")

    # Étape 4 : Générer le résumé final (avec le modèle choisi par l'utilisateur)
    log(f"📊 ÉTAPE 3/3 - Génération du résumé final")
    log(f"   ℹ️  Modèle de synthèse: {model_choice}")
    log(f"   ℹ️  Type de prompt: {prompt_type}")
    if progress_callback:
        progress_callback("Génération du résumé final...")

    final_system_prompt = build_final_system_prompt(prompt_type)
    final_user_prompt = build_final_user_prompt(
        extracted_jsons,
        mode="resume_global",
        max_pages_hint=5
    )

    final_prompt_tokens = approx_tokens_simple(final_user_prompt)
    log(f"   └─ Tokens du prompt final: ~{final_prompt_tokens:,}")
    log(f"   └─ 📡 Envoi requête API finale ({model_choice})...")

    messages = [{"role": "user", "content": final_user_prompt}]
    final_response = call_model(model_choice, final_system_prompt, messages)

    final_response_tokens = approx_tokens_simple(final_response)
    log(f"   └─ 📥 Réponse finale reçue: ~{final_response_tokens:,} tokens")

    print("\n" + "="*60, flush=True)
    log(f"✅ PIPELINE TERMINÉ")
    log(f"   📄 {tokens_original:,} tokens → 📦 {tokens_compressed:,} tokens → 📝 {final_response_tokens:,} tokens")
    print("="*60 + "\n", flush=True)

    return {
        "nb_sections": nb_sections,
        "nb_packets": nb_packets,
        "extracted_jsons": extracted_jsons,
        "final_response": final_response,
        "tokens_original": tokens_original,
        "tokens_compressed": tokens_compressed,
        "compression_ratio": compression_ratio
    }


# Créer les onglets
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "📄 Fichiers de conclusions", "✏️ Prompt personnalisable", "📐 Modèle de trame", "📖 Guide d'utilisation"])

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
            # Afficher les infos de debug si disponibles (Mistral Small 4)
            if "debug_info" in message:
                debug = message["debug_info"]
                finish_reason = debug.get("finish_reason", "")
                usage_info = debug.get("usage", "")
                if finish_reason == "length":
                    st.warning(f"⚠️ **Réponse tronquée** (finish_reason: `{finish_reason}`) - {usage_info}")
                else:
                    st.info(f"✅ finish_reason: `{finish_reason}` - {usage_info}")

            # Afficher les infos de compression si disponibles
            if "compression_info" in message:
                comp_info = message["compression_info"]
                tokens_orig = comp_info.get('tokens_original', 0)
                tokens_comp = comp_info.get('tokens_compressed', 0)
                ratio = comp_info.get('compression_ratio', 0)
                st.success(
                    f"📦 **Mode compression** : {comp_info['nb_sections']} sections → {comp_info['nb_packets']} paquet(s)\n\n"
                    f"📊 **Tokens** : {tokens_orig:,} → {tokens_comp:,} (**{ratio}%** de réduction)"
                )
                with st.expander("🔍 Voir les données intermédiaires extraites"):
                    for i, packet_json in enumerate(comp_info.get("extracted_jsons", [])):
                        st.markdown(f"**Paquet {i+1}**")
                        if "error" in packet_json:
                            st.warning(f"Erreur d'extraction : {packet_json['error']}")
                        else:
                            st.json(packet_json)

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

            # Boutons d'action : Copier + Feedback
            col_copy, col_feedback = st.columns([1, 1])
            with col_copy:
                copy_button(content, f"copy_btn_{idx}")
            with col_feedback:
                st.link_button("📝 Donner votre avis", tally_url, type="secondary", use_container_width=True)

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

        # Vérifier le nombre de tokens avant l'appel (sauf en mode compression)
        should_proceed = True

        if not enable_compression:
            # Mode normal : vérifier la limite de tokens
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
                should_proceed = False
            else:
                # Afficher info tokens dans la sidebar
                st.sidebar.info(f"📊 Tokens estimés : {estimated_tokens:,} / {token_limit:,}")
        else:
            # Mode compression : pas de limite de tokens
            # Le document sera découpé en paquets respectant les limites
            st.sidebar.success(f"📦 Mode compression : pas de limite de tokens")

        # Générer et afficher la réponse si autorisé
        if should_proceed:
            # Générer et afficher la réponse
            with st.chat_message("assistant"):
                try:
                    # Vérifier si le mode compression est activé
                    if enable_compression:
                        # Déterminer le type de prompt compression
                        if "Rapport de synthèse" in prompt_choice:
                            compression_prompt_type = "rapport_synthese"
                        else:
                            compression_prompt_type = "resume_conclusions"

                        # Pipeline de compression pour documents longs
                        progress_placeholder = st.empty()

                        def update_progress(msg):
                            progress_placeholder.info(f"📦 {msg}")

                        with st.spinner("Pipeline de compression en cours..."):
                            result = call_model_with_compression(
                                model_choice,
                                user_query,
                                prompt_type=compression_prompt_type,
                                progress_callback=update_progress
                            )

                        progress_placeholder.empty()

                        # Afficher les statistiques de compression avec les tokens
                        st.success(
                            f"✅ Compression terminée : {result['nb_sections']} sections → {result['nb_packets']} paquet(s)\n\n"
                            f"📊 **Tokens** : {result['tokens_original']:,} → {result['tokens_compressed']:,} "
                            f"(**{result['compression_ratio']}%** de réduction)"
                        )

                        # Stocker les infos de compression pour affichage ultérieur
                        compression_info = {
                            "nb_sections": result["nb_sections"],
                            "nb_packets": result["nb_packets"],
                            "extracted_jsons": result["extracted_jsons"],
                            "tokens_original": result["tokens_original"],
                            "tokens_compressed": result["tokens_compressed"],
                            "compression_ratio": result["compression_ratio"]
                        }

                        response_text = result["final_response"]

                    else:
                        # Appel simple (1 étape)
                        with st.spinner("Génération de la réponse..."):
                            response_text = call_model(
                                model_choice,
                                system_prompt,
                                st.session_state.messages
                            )

                    # Récupérer les infos de debug si disponibles (Mistral Small 4)
                    debug_info = None
                    if "debug_finish_reason" in st.session_state:
                        finish_reason = st.session_state.pop("debug_finish_reason")
                        usage_info = st.session_state.pop("debug_usage", "")
                        debug_info = {
                            "finish_reason": finish_reason,
                            "usage": usage_info
                        }

                    # Ajouter la réponse à l'historique (avec debug_info et compression_info si disponibles)
                    message_data = {"role": "assistant", "content": response_text}
                    if debug_info:
                        message_data["debug_info"] = debug_info
                    if enable_compression and 'compression_info' in dir():
                        message_data["compression_info"] = compression_info
                    st.session_state.messages.append(message_data)

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

# ============================================================
# ONGLET 3 : PROMPT PERSONNALISABLE
# ============================================================
with tab3:
    st.header("Prompt personnalisable")
    st.markdown("""
    Créez votre propre prompt système pour personnaliser le comportement de l'assistant.
    Une fois sauvegardé, sélectionnez **"Prompt personnalisable"** dans la liste des prompts système de la barre latérale.
    """)

    # Zone d'édition du prompt personnalisé
    new_custom_prompt = st.text_area(
        "Votre prompt personnalisé",
        value=st.session_state.custom_prompt,
        height=400,
        key="custom_prompt_editor",
        help="Décrivez le comportement souhaité de l'assistant. Par exemple : 'Vous êtes un expert en droit du travail...'"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
            st.session_state.custom_prompt = new_custom_prompt
            st.success("✅ Prompt personnalisé sauvegardé !")
            st.rerun()
    with col2:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            st.session_state.custom_prompt = "Vous êtes un assistant juridique. Répondez aux questions de l'utilisateur de manière précise et professionnelle."
            st.success("✅ Prompt réinitialisé !")
            st.rerun()

    # Afficher un aperçu
    with st.expander("📋 Aperçu du prompt actuel"):
        st.code(st.session_state.custom_prompt, language=None)

    # Compteur de caractères
    st.caption(f"📊 {len(st.session_state.custom_prompt):,} caractères | ~{len(st.session_state.custom_prompt) // 4:,} tokens estimés")

# ============================================================
# ONGLET 4 : MODÈLE DE TRAME
# ============================================================
with tab4:
    st.header("Modèle de trame")
    st.markdown("""
    Définissez ici la **trame** (structure et ordre des sections) pour la rédaction de l'exposé du litige.

    Cette trame sera **automatiquement insérée** dans le prompt lorsque vous sélectionnerez
    **"Rédaction Exposé du Litige"** dans la liste des prompts système.
    """)

    # Avertissement si le prompt n'est pas sélectionné
    if prompt_choice != "Rédaction Exposé du Litige":
        st.info("💡 Pour utiliser cette trame, sélectionnez **\"Rédaction Exposé du Litige\"** dans la liste des prompts système de la barre latérale.")

    # Zone d'édition de la trame
    new_custom_trame = st.text_area(
        "Votre trame personnalisée",
        value=st.session_state.custom_trame,
        height=450,
        key="custom_trame_editor",
        help="Définissez la structure de l'exposé du litige : titres des sections, ordre, et consignes spécifiques pour chaque partie."
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Sauvegarder", type="primary", use_container_width=True, key="save_trame"):
            st.session_state.custom_trame = new_custom_trame
            st.success("✅ Trame sauvegardée !")
            st.rerun()
    with col2:
        if st.button("🔄 Réinitialiser", use_container_width=True, key="reset_trame"):
            st.session_state.custom_trame = """[TRAME À COMPLÉTER]

Renseignez ici la structure de l'exposé du litige que vous souhaitez obtenir.

Exemple :
## I. EXPOSÉ DU LITIGE
### A. Les faits
[Consignes pour cette section...]

### B. La procédure
[Consignes pour cette section...]

### C. Les prétentions des parties
[Consignes pour cette section...]

### D. Les moyens des parties
[Consignes pour cette section...]
"""
            st.success("✅ Trame réinitialisée !")
            st.rerun()

    # Afficher un aperçu
    with st.expander("📋 Aperçu de la trame actuelle"):
        st.markdown(st.session_state.custom_trame)

    # Compteur de caractères
    st.caption(f"📊 {len(st.session_state.custom_trame):,} caractères | ~{len(st.session_state.custom_trame) // 4:,} tokens estimés")

# ============================================================
# ONGLET 5 : GUIDE D'UTILISATION
# ============================================================
with tab5:
    st.header("Guide d'utilisation")
    st.markdown("""
### Mode d'emploi de Streamlit : comment tester les LLM

**Utiliser exclusivement les conclusions anonymisées pour les tests**

#### Étapes pour tester :

1. **Choisir un modèle et un prompt** dans la barre latérale

2. **Faire une phrase introductive**, par exemple :
   > *"Peux-tu résumer les conclusions jointes en respectant les consignes du prompt ? Voici les conclusions de l'appelante"*

3. **Coller les conclusions anonymisées** dans la zone de saisie

4. **Copier le résultat obtenu** dans un document Word qui sera intitulé selon les consignes ci-dessous

5. **Analyser le résultat** en comparant avec les conclusions :
   - Vous pouvez faire des commentaires sur le document Word en soulignant les erreurs, les interprétations, les approximations juridiques, etc.
   - Pour effectuer la comparaison, ouvrir les conclusions non anonymisées (c'est plus facile)
   - Ne pas trop s'attarder sur la conformité des prétentions : un autre système que l'IA pourra les reprendre in extenso

6. **Répondre au questionnaire** (bouton "Donner votre avis" après chaque réponse)

7. **Poursuivre la conversation** si nécessaire en demandant à l'IA d'améliorer sa réponse, puis répondre à nouveau au questionnaire

8. **Ajouter des compléments sur Notion** dans la cellule réservée si vous avez des nouveaux commentaires

9. **Glisser le document Word sur Notion**

---

### Répéter l'opération

Pour les autres conclusions et prompts, cliquer sur **"Nouvelle conversation"** à chaque fois.

💡 **Conseil** : Il est plus efficace de tester pour chaque prompt les différents LLM. Cela permet aussi de copier-coller la question posée.

---

### Intitulé des documents Word

Les résultats obtenus seront copiés dans un document Word intitulé selon ce format :

```
[N° Dossier] [NOM DU PROMPT] [appelant ou intimé] [Initiales]
```

**Exemples :**
- `6 synthèse faits proced prétention`
- `6 synthèse des moyens`
- `6 exposé du litige avec sans trame`

---

### Mode d'emploi de Notion

- Chaque testeur dispose d'une vue avec son nom → cliquer dessus et remplir les cellules
- **Pour glisser un document** :
  1. Cliquer sur le bouton avec 6 points
  2. Puis **OUVRIR** dans aperçu latéral
  3. Cliquer sur **Ajouter un commentaire**
  4. Puis sur le **trombone** 📎
  5. Sélectionner votre fichier

📝 *L'enregistrement est automatique*
    """)

# Information sur les clés API dans la sidebar
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ Configuration des clés API"):
    st.write("""
    Pour utiliser cette application, vous devez configurer les clés API suivantes
    dans vos variables d'environnement :

    - `MISTRAL_API_KEY` pour Mixtral 8x22B
    - `NEBIUS_API_KEY` pour GPT-OSS-120B

    Vous pouvez les définir dans un fichier `.env` à la racine du projet.
    """)
