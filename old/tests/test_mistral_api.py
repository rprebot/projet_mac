"""Test rapide pour vérifier que mistral-large-latest fonctionne avec la clé API."""

import os
import time
from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    print("MISTRAL_API_KEY non trouvée dans .env")
    exit(1)

print(f"Clé API chargée ({len(api_key)} caractères)")
print("Test de mistral-large-latest avec system prompt juridique...")
print()

# System prompt complet
SYSTEM_PROMPT = open(os.path.join(os.path.dirname(__file__), "test_system_prompt.md"), "r").read()

USER_PROMPT = "quel est le temps de travail minimal pour un apprenti?"

client = Mistral(api_key=api_key)

print(f"System prompt : {len(SYSTEM_PROMPT)} caractères")
print(f"Question : {USER_PROMPT}")
print()
print("Envoi de la requête...")

start = time.time()
response = client.chat.complete(
    model="mistral-large-latest",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT},
    ],
)
elapsed = time.time() - start

print(f"Modèle utilisé : {response.model}")
print(f"Temps de réponse : {elapsed:.1f}s")
print(f"Tokens usage : prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")
print()
print("=" * 80)
print("RÉPONSE :")
print("=" * 80)
print(response.choices[0].message.content)
