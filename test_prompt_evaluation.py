"""
Script pour tester et évaluer le prompt "Résumé Conclusions"
avec Mistral-medium-2508 et évaluation Magistral
"""

import os
import json
from mistralai import Mistral
from dotenv import load_dotenv
import re

# Charger les variables d'environnement
load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

def load_prompt(prompt_file):
    """Charge le prompt depuis un fichier"""
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()

def load_document(doc_file):
    """Charge un document de test"""
    with open(doc_file, 'r', encoding='utf-8') as f:
        return f.read()

def load_evaluation_criteria():
    """Charge les critères d'évaluation"""
    with open("evaluation_criteria.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def load_evaluation_prompt():
    """Charge le prompt d'évaluation"""
    with open("prompts/evaluation_prompt.md", 'r', encoding='utf-8') as f:
        return f.read()

def generate_summary(system_prompt, document, model="mistral-medium-2508"):
    """Génère un résumé avec Mistral-medium-2508"""
    print(f"\n🤖 Génération du résumé avec {model}...")

    client = Mistral(api_key=MISTRAL_API_KEY)
    response = client.chat.complete(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": document}
        ]
    )

    return response.choices[0].message.content

def evaluate_with_magistral(document_source, reponse_llm, criteria):
    """Évalue la réponse avec Magistral Medium"""
    print("\n🎯 Évaluation avec Magistral Medium...")

    # Charger le template du prompt d'évaluation
    prompt_template = load_evaluation_prompt()

    # Construire la liste des critères pour le prompt
    criteres_text = "\n".join([f"- **{nom}** : {description}" for nom, description in criteria["criteres"]])
    criteres_json = ", ".join([f'"{nom}": <note 1-5>' for nom, _ in criteria["criteres"]])

    # Formater le prompt avec les variables
    evaluation_prompt = prompt_template.format(
        task_description=criteria["description"],
        document_source=document_source[:15000],  # Limiter la taille
        reponse_llm=reponse_llm,
        criteres_text=criteres_text,
        criteres_json=criteres_json
    )

    client = Mistral(api_key=MISTRAL_API_KEY)
    response = client.chat.complete(
        model="magistral-medium-2506",
        messages=[{"role": "user", "content": evaluation_prompt}]
    )

    message = response.choices[0].message
    message_content = message.content

    # Extraire la réponse
    response_text = ""
    reasoning_text = ""

    if isinstance(message_content, list):
        for item in message_content:
            item_type = getattr(item, 'type', None)

            if item_type == 'thinking':
                thinking_content = getattr(item, 'thinking', [])
                for think_item in thinking_content:
                    if hasattr(think_item, 'text'):
                        reasoning_text += think_item.text

            elif item_type == 'text':
                if hasattr(item, 'text'):
                    response_text += item.text

            elif hasattr(item, 'text'):
                response_text += item.text

    elif isinstance(message_content, str):
        response_text = message_content

    # Si pas de réponse texte, utiliser le raisonnement
    if not response_text and reasoning_text:
        response_text = reasoning_text

    # Nettoyer les backticks markdown
    if "```json" in response_text:
        match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if match:
            response_text = match.group(1)
    elif "```" in response_text:
        match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
        if match:
            response_text = match.group(1)

    # Extraire le JSON
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1

    if json_start != -1 and json_end > json_start:
        json_str = response_text[json_start:json_end]
        try:
            evaluation = json.loads(json_str)
            return evaluation
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON: {e}")
            print(f"Réponse brute: {response_text[:500]}")
            return {"error": f"Erreur parsing JSON: {str(e)}"}
    else:
        return {"error": "Pas de JSON trouvé", "raw": response_text[:500]}

def display_evaluation(eval_result, doc_name):
    """Affiche les résultats de l'évaluation"""
    print(f"\n{'='*60}")
    print(f"📊 RÉSULTATS POUR: {doc_name}")
    print(f"{'='*60}")

    if "error" in eval_result:
        print(f"❌ Erreur: {eval_result['error']}")
        return

    # Score global
    score_global = eval_result.get("score_global", "N/A")
    print(f"\n🎯 Score global: {score_global}/5")

    # Scores par critère
    print("\n📋 Scores par critère:")
    scores = eval_result.get("scores", {})
    raisonnements = eval_result.get("raisonnements", {})

    for critere, score in scores.items():
        emoji = "✅" if score >= 4 else "⚠️" if score >= 3 else "❌"
        print(f"  {emoji} {critere}: {score}/5")
        if critere in raisonnements:
            print(f"     → {raisonnements[critere]}")

    # Points forts
    print("\n✅ Points forts:")
    for point in eval_result.get("points_forts", []):
        print(f"  • {point}")

    # Points à améliorer
    print("\n⚠️ Points à améliorer:")
    for point in eval_result.get("points_amelioration", []):
        print(f"  • {point}")

    # Synthèse
    print(f"\n📝 Synthèse: {eval_result.get('synthese', '')}")
    print(f"\n{'='*60}\n")

    return eval_result

def main():
    """Fonction principale"""
    print("🚀 Démarrage des tests d'évaluation du prompt 'Résumé Conclusions'\n")

    if not MISTRAL_API_KEY:
        print("❌ Erreur: MISTRAL_API_KEY non configurée")
        return

    # Charger le prompt système
    system_prompt = load_prompt("prompts/resume_conclusions.md")
    print("✅ Prompt système chargé")

    # Charger les critères d'évaluation
    criteria = load_evaluation_criteria()["Résumé Conclusions"]
    print("✅ Critères d'évaluation chargés")

    # Liste des documents à tester (commencer par les plus petits)
    test_documents = [
        "dossiers/Dossier_4_conclusion_intimee.txt",  # 18K
        "dossiers/Dossier_4_conclusion_appelante.txt",  # 24K
    ]

    results = []

    for doc_path in test_documents:
        doc_name = os.path.basename(doc_path)
        print(f"\n{'#'*60}")
        print(f"📄 Test sur: {doc_name}")
        print(f"{'#'*60}")

        try:
            # Charger le document
            document = load_document(doc_path)
            print(f"✅ Document chargé ({len(document)} caractères)")

            # Générer le résumé
            summary = generate_summary(system_prompt, document)
            print(f"✅ Résumé généré ({len(summary)} caractères)")

            # Sauvegarder le résumé
            output_file = f"test_output_{doc_name.replace('.txt', '_resume.txt')}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"💾 Résumé sauvegardé dans: {output_file}")

            # Évaluer avec Magistral
            evaluation = evaluate_with_magistral(document, summary, criteria)

            # Afficher les résultats
            eval_result = display_evaluation(evaluation, doc_name)

            results.append({
                "document": doc_name,
                "evaluation": eval_result,
                "summary_length": len(summary)
            })

        except Exception as e:
            print(f"❌ Erreur lors du traitement de {doc_name}: {str(e)}")
            import traceback
            traceback.print_exc()

    # Résumé global
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ GLOBAL DES TESTS")
    print(f"{'='*60}")

    for result in results:
        if "error" not in result["evaluation"]:
            score = result["evaluation"].get("score_global", "N/A")
            print(f"  {result['document']}: {score}/5")

    print("\n✅ Tests terminés!")

if __name__ == "__main__":
    main()
