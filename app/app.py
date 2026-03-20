import streamlit as st
import streamlit.components.v1 as components
import os
import json
import html
from urllib.parse import urlencode
from openai import OpenAI
from mistralai import Mistral
import requests
from dotenv import load_dotenv
import tiktoken

# Charger les variables d'environnement depuis .env
load_dotenv()


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
    "Résumé Conclusions": "prompts/resume_conclusions.md",
    "Synthèse Faits & Procédure": "prompts/synthese_faits_procedure.md",
    "Synthèse Moyens": "prompts/synthese_moyens.md",
    "Rapport de synthèse": "prompts/synthese_faits_procedure_moyens.md",
    "Rédaction Exposé du Litige": "prompts/redaction_expose_litige.md"
}

# Prompts chaînés (2 étapes)
CHAINED_PROMPTS = {
    "Résumé Conclusions (2 étapes)": {
        "etape1": "prompts_chaines/resume_conclusions_etape1_structure.md",
        "etape2": "prompts_chaines/resume_conclusions_etape2_resume.md"
    }
}

def load_chained_prompts():
    """
    Charge les prompts chaînés (2 étapes) depuis les fichiers markdown
    """
    prompts = {}
    for name, files in CHAINED_PROMPTS.items():
        prompts[name] = {}
        for etape, filename in files.items():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    prompts[name][etape] = f.read()
            except FileNotFoundError:
                prompts[name][etape] = f"Erreur : Le fichier {filename} n'a pas été trouvé."
    return prompts

# Charger les prompts chaînés
SYSTEM_PROMPTS_CHAINED = load_chained_prompts()

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
        ("Synthèse Moyens", "prompts/synthese_moyens.md"),
        ("Rapport de synthèse", "prompts/synthese_faits_procedure_moyens.md"),
        ("Rédaction Exposé du Litige", "prompts/redaction_expose_litige.md")
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
        "Dossier 5 - Leonard (Employeur)": "dossiers/Dossier_5_Leonard_(employeur).txt",
        "Dossier 5 - Leonard (Salarié)": "dossiers/Dossier_5_Leonard_(salarie).txt",
        "Dossier 6 - Conclusion Appelant": "dossiers/Dossier_6_conclusion_appelant.txt",
        "Dossier 6 - Conclusion Intimée": "dossiers/Dossier_6_conclusion_intimee.txt",
        "Dossier 7 - Conclusion Appelante": "dossiers/Dossier_7_conculsion_appelante.txt",
        "Dossier 7 - Conclusion Intimée": "dossiers/Dossier_7_conclusion_intimee.txt",
        "Dossier 8 - Demandeur": "dossiers/Dossier_8_demandeur.txt",
        "Dossier 8 - Intimée": "dossiers/Dossier_8_intimee.txt",
        "Dossier 9-2 - Demandeur": "dossiers/Dossier_9-2_demandeur.txt",
        "Dossier 9-2 - Défendeur": "dossiers/Dossier_9-2_defendeur.txt",
        "Dossier 13 - Conclusion Défendeur": "dossiers/dossier_13_conclusion_defendeur.txt",
        "Dossier 14 - Défendeur": "dossiers/Doissier 14 - defendeur.txt",
        "Dossier 14 - Demandeur": "dossiers/Dossier 14 - demandeur.txt",
        "Dossier 15 - Défendeur": "dossiers/Dossier_15_defendeur.txt",
        "Dossier 15 - Demandeur": "dossiers/Dossier_15_demandeur.txt",
        "Dossier 17-3 - Assignation": "dossiers/Dossier_17-3_Dossier  assignation sans def .txt"
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
    ["Mixtral 8x22B (Mistral)", "Mistral-medium-2508", "Mistral Large 2", "Mistral Small 4", "GPT-OSS-120B (Nebius)", "Nemotron Super 120B (Nebius)"]
)

# Sélection du prompt système (incluant le prompt personnalisable)
# Note: les prompts chaînés (2 étapes) sont désactivés pour l'instant mais le code reste disponible
prompt_options = list(SYSTEM_PROMPTS.keys()) + ["Prompt personnalisable"]
prompt_choice = st.sidebar.selectbox(
    "Prompt système",
    prompt_options
)

# Indicateur si le prompt sélectionné est un prompt chaîné
is_chained_prompt = prompt_choice in CHAINED_PROMPTS

# Récupérer le prompt système sélectionné
if prompt_choice == "Prompt personnalisable":
    system_prompt = st.session_state.custom_prompt
elif is_chained_prompt:
    # Pour les prompts chaînés, on utilise le prompt de l'étape 1 comme référence
    system_prompt = SYSTEM_PROMPTS_CHAINED[prompt_choice]["etape1"]
elif prompt_choice == "Rédaction Exposé du Litige":
    # Insérer automatiquement la trame de l'utilisateur dans le prompt
    base_prompt = SYSTEM_PROMPTS[prompt_choice]
    # Remplacer le placeholder par la trame de l'utilisateur
    trame_placeholder = """```
[TRAME À COMPLÉTER PAR L'UTILISATEUR]

Insérez ici la structure et les consignes spécifiques pour la rédaction de l'exposé du litige.

Exemple de trame possible :
- Section 1 : [Titre et consignes]
- Section 2 : [Titre et consignes]
- Section 3 : [Titre et consignes]
- ...

```"""
    system_prompt = base_prompt.replace(trame_placeholder, f"```\n{st.session_state.custom_trame}\n```")
else:
    system_prompt = SYSTEM_PROMPTS[prompt_choice]

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
            filename = PROMPT_FILES.get(prompt_choice)
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(edited_prompt)
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
    # Construire les messages avec le système + historique
    full_messages = [{"role": "system", "content": system_prompt}] + messages_history

    # Mixtral 8x22B via Mistral
    if model_choice == "Mixtral 8x22B (Mistral)":
        if not MISTRAL_API_KEY:
            raise ValueError("La clé API Mistral n'est pas configurée.")

        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=full_messages,
            temperature=0.3
        )
        return response.choices[0].message.content

    # Mistral Medium 2508 (modèle assistant numérique)
    elif model_choice == "Mistral-medium-2508":
        if not MISTRAL_API_KEY:
            raise ValueError("La clé API Mistral n'est pas configurée.")

        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-medium-2508",
            messages=full_messages,
            temperature=0.3
        )
        return response.choices[0].message.content

    # Mistral Large 2 (modèle flagship)
    elif model_choice == "Mistral Large 2":
        if not MISTRAL_API_KEY:
            raise ValueError("La clé API Mistral n'est pas configurée.")

        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-large-2411",
            messages=full_messages,
            temperature=0.3
        )
        return response.choices[0].message.content

    # Mistral Small 4 (modèle compact performant)
    elif model_choice == "Mistral Small 4":
        if not MISTRAL_API_KEY:
            raise ValueError("La clé API Mistral n'est pas configurée.")

        # Renforcer l'instruction de style littéraire pour ce modèle
        style_instruction = """

⚠️ INSTRUCTION CRITIQUE DE STYLE :
Tu dois IMPÉRATIVEMENT rédiger en PROSE LITTÉRAIRE avec des paragraphes fluides et continus.
- INTERDIT : les listes à puces, les tirets, les numérotations (sauf pour les prétentions/dispositif)
- OBLIGATOIRE : des phrases complètes reliées par des connecteurs logiques (En effet, Par ailleurs, Toutefois, Dès lors, En outre, De surcroît)
- Le texte doit ressembler à un arrêt de cour d'appel, PAS à des notes ou un plan.
"""
        enhanced_system_prompt = system_prompt + style_instruction
        enhanced_messages = [{"role": "system", "content": enhanced_system_prompt}] + messages_history

        client = Mistral(api_key=MISTRAL_API_KEY)
        response = client.chat.complete(
            model="mistral-small-2603",
            messages=enhanced_messages,
            temperature=0.3,
            max_tokens=65536  # Augmenté pour éviter la troncature
        )
        # Debug: stocker la raison d'arrêt pour affichage
        finish_reason = response.choices[0].finish_reason
        usage = response.usage
        st.session_state["debug_finish_reason"] = finish_reason
        st.session_state["debug_usage"] = f"Tokens: {usage.prompt_tokens} (prompt) + {usage.completion_tokens} (completion) = {usage.total_tokens} (total)"

        # Log console pour debug supplémentaire
        print(f"[DEBUG Mistral Small 4] finish_reason={finish_reason}, completion_tokens={usage.completion_tokens}, max_tokens=65536")

        return response.choices[0].message.content

    # GPT-OSS-120B via Nebius (OpenAI compatible) avec reasoning
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
            temperature=0.3,
            extra_body={
                "reasoning": {
                    "effort": "high"
                }
            }
        )
        return response.choices[0].message.content

    # Nemotron Super 120B via Nebius (OpenAI compatible)
    elif model_choice == "Nemotron Super 120B (Nebius)":
        if not NEBIUS_API_KEY:
            raise ValueError("La clé API Nebius n'est pas configurée.")

        client = OpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=NEBIUS_API_KEY
        )
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b",
            messages=full_messages,
            temperature=0.3
        )
        return response.choices[0].message.content


def call_model_chained(model_choice, prompt_choice, user_query):
    """
    Appelle le modèle en 2 étapes pour les prompts chaînés.
    Étape 1 : Extraction de la structure
    Étape 2 : Résumé avec la structure fournie
    Retourne un dictionnaire avec les résultats des 2 étapes.
    """
    prompts = SYSTEM_PROMPTS_CHAINED[prompt_choice]

    # ÉTAPE 1 : Extraction de la structure
    prompt_etape1 = prompts["etape1"]
    messages_etape1 = [{"role": "user", "content": user_query}]

    structure_extraite = call_model(model_choice, prompt_etape1, messages_etape1)

    # ÉTAPE 2 : Résumé avec la structure fournie
    prompt_etape2 = prompts["etape2"]

    # Construire le message pour l'étape 2 avec le document ET la structure
    message_etape2 = f"""## DOCUMENT SOURCE (Conclusion juridique)

{user_query}

---

## STRUCTURE EXTRAITE (À suivre impérativement)

{structure_extraite}
"""

    messages_etape2 = [{"role": "user", "content": message_etape2}]

    resume_final = call_model(model_choice, prompt_etape2, messages_etape2)

    return {
        "etape1_structure": structure_extraite,
        "etape2_resume": resume_final
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
                try:
                    # Vérifier si c'est un prompt chaîné (2 étapes)
                    if is_chained_prompt:
                        # Appel chaîné en 2 étapes
                        with st.spinner("Analyse en 2 étapes en cours..."):
                            result = call_model_chained(model_choice, prompt_choice, user_query)

                        # Afficher uniquement le résultat de l'étape 2
                        response_text = result["etape2_resume"]
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

                    # Ajouter la réponse à l'historique (avec debug_info si disponible)
                    message_data = {"role": "assistant", "content": response_text}
                    if debug_info:
                        message_data["debug_info"] = debug_info
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
