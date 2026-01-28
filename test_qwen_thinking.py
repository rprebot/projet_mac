"""
Script pour tester le format de réponse de QwQ-32B (modèle de raisonnement)
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")

def test_qwen_thinking():
    """Teste l'appel à Qwen et affiche la structure complète de la réponse"""

    if not NEBIUS_API_KEY:
        print("❌ Erreur: NEBIUS_API_KEY non configurée")
        return

    print("🧪 Test de QwQ-32B (modèle de raisonnement)\n")

    client = OpenAI(
        base_url="https://api.studio.nebius.ai/v1/",
        api_key=NEBIUS_API_KEY
    )

    # Question simple pour tester
    messages = [
        {"role": "user", "content": "Résous cette équation: 2x + 5 = 15"}
    ]

    print("📤 Envoi de la requête...\n")

    # Test 1: Sans extra_body
    print("Test 1: Sans extra_body (défaut)")
    print("-" * 60)

    response = client.chat.completions.create(
        model="Qwen/Qwen3-32B-fast",
        messages=messages,
        temperature=0.7
    )

    print(f"Contient <think>: {'<think>' in response.choices[0].message.content}")
    print(f"Longueur: {len(response.choices[0].message.content)} caractères")
    print()

    # Test 2: Avec extra_body enable_thinking=True
    print("\nTest 2: Avec extra_body enable_thinking=True")
    print("-" * 60)

    response2 = client.chat.completions.create(
        model="Qwen/Qwen3-32B-fast",
        messages=messages,
        temperature=0.7,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": True
            }
        }
    )

    print(f"Contient <think>: {'<think>' in response2.choices[0].message.content}")
    print(f"Longueur: {len(response2.choices[0].message.content)} caractères")

    # Utiliser la seconde réponse pour le reste du test
    response = response2

    print("✅ Réponse reçue!\n")
    print("="*60)
    print("📋 STRUCTURE DE LA RÉPONSE")
    print("="*60)

    # Examiner la structure complète
    message = response.choices[0].message

    print(f"\n1. Message object type: {type(message)}")
    print(f"2. Message attributes: {dir(message)}")

    # Contenu principal
    print(f"\n3. Content:")
    print(f"   Type: {type(message.content)}")
    print(f"   Valeur:")
    print("-" * 60)
    print(message.content)
    print("-" * 60)

    # Vérifier s'il y a d'autres champs
    if hasattr(message, 'role'):
        print(f"\n4. Role: {message.role}")

    if hasattr(message, 'tool_calls'):
        print(f"\n5. Tool calls: {message.tool_calls}")

    if hasattr(message, 'function_call'):
        print(f"\n6. Function call: {message.function_call}")

    # Vérifier la réponse complète
    print("\n" + "="*60)
    print("📦 RÉPONSE COMPLÈTE (response object)")
    print("="*60)

    print(f"\nResponse attributes: {dir(response)}")

    if hasattr(response, 'usage'):
        print(f"\nUsage: {response.usage}")

    # Chercher les balises thinking
    content = message.content or ""

    print("\n" + "="*60)
    print("🔍 ANALYSE DES BALISES")
    print("="*60)

    print(f"\nLongueur du contenu: {len(content)} caractères")

    # Chercher différentes variantes de balises thinking
    variants = [
        "<think>",
        "<thinking>",
        "<thought>",
        "思考：",  # Chinois
        "[THINKING]",
        "**Thinking:**"
    ]

    for variant in variants:
        if variant in content:
            print(f"✅ Trouvé: {variant}")
        else:
            print(f"❌ Pas trouvé: {variant}")

    # Afficher les 500 premiers caractères
    print("\n" + "="*60)
    print("📝 DÉBUT DU CONTENU (500 premiers caractères)")
    print("="*60)
    print(content[:500])
    print("...")

if __name__ == "__main__":
    test_qwen_thinking()
