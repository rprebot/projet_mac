"""
Script pour vérifier l'usage de l'API Mistral
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Charger les variables d'environnement
load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

def check_usage():
    """Vérifie l'usage de l'API Mistral"""

    if not MISTRAL_API_KEY:
        print("❌ Erreur: MISTRAL_API_KEY non configurée")
        return

    print("🔍 Vérification de l'usage de l'API Mistral...\n")

    # URL de l'API Mistral pour l'usage
    url = "https://api.mistral.ai/v1/usage"

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Paramètres pour la période (dernières 24h par défaut)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Derniers 7 jours

    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }

    try:
        print(f"📅 Période: {params['start_date']} à {params['end_date']}\n")

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            print("✅ Données récupérées avec succès!\n")
            print("="*60)
            print("📊 USAGE DE L'API MISTRAL")
            print("="*60)

            # Afficher les données brutes pour voir la structure
            import json
            print(json.dumps(data, indent=2))

        elif response.status_code == 404:
            print("⚠️ Endpoint /v1/usage non disponible")
            print("Essai avec l'endpoint alternatif...\n")

            # Essayer l'endpoint de billing
            url_billing = "https://api.mistral.ai/v1/billing/usage"
            response = requests.get(url_billing, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                print("✅ Données récupérées!\n")
                import json
                print(json.dumps(data, indent=2))
            else:
                print(f"❌ Erreur {response.status_code}: {response.text}")

        else:
            print(f"❌ Erreur {response.status_code}")
            print(f"Réponse: {response.text}\n")

            if response.status_code == 429:
                print("⚠️ Rate limit atteint même pour la consultation de l'usage!")
                print("→ Attendez quelques minutes avant de réessayer")

    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()

def check_account_info():
    """Vérifie les informations du compte"""

    print("\n" + "="*60)
    print("👤 INFORMATIONS DU COMPTE")
    print("="*60 + "\n")

    url = "https://api.mistral.ai/v1/models"

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print("✅ Modèles disponibles:\n")

            models = data.get("data", [])
            for model in models:
                model_id = model.get("id", "N/A")
                print(f"  • {model_id}")

        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

def test_simple_call():
    """Fait un appel simple pour voir les headers de réponse (limites)"""

    print("\n" + "="*60)
    print("🧪 TEST D'APPEL SIMPLE (pour voir les limites)")
    print("="*60 + "\n")

    from mistralai import Mistral

    try:
        client = Mistral(api_key=MISTRAL_API_KEY)

        # Appel très simple (peu de tokens)
        print("Envoi d'une requête test avec mistral-medium-2508...\n")

        response = client.chat.complete(
            model="mistral-medium-2508",
            messages=[{"role": "user", "content": "Bonjour"}]
        )

        print("✅ Réponse reçue!")
        print(f"Réponse: {response.choices[0].message.content}\n")

        # Les limites sont parfois dans les headers HTTP
        # Mais le SDK Mistral ne les expose pas directement
        print("ℹ️  Pour voir les limites exactes, consultez:")
        print("   https://console.mistral.ai/usage")
        print("   ou")
        print("   https://console.mistral.ai/limits\n")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erreur: {error_msg}\n")

        if "429" in error_msg or "Rate limit" in error_msg:
            print("⚠️ RATE LIMIT DÉPASSÉ!")
            print("\nInformations probables:")
            print("  • Vous avez fait trop de requêtes récemment")
            print("  • Attendez 1-2 minutes avant de réessayer")
            print("  • Vérifiez votre plan sur https://console.mistral.ai/")

def main():
    print("🚀 Diagnostic de l'usage de l'API Mistral\n")

    # 1. Vérifier l'usage
    check_usage()

    # 2. Vérifier les modèles disponibles
    check_account_info()

    # 3. Test simple
    test_simple_call()

    print("\n" + "="*60)
    print("📌 RECOMMANDATIONS")
    print("="*60)
    print("""
1. Consultez votre dashboard Mistral:
   → https://console.mistral.ai/usage
   → https://console.mistral.ai/limits

2. Vérifiez vos limites par modèle:
   • mistral-medium-2508 (votre modèle principal)
   • magistral-medium-2506 (modèle d'évaluation)

3. Si vous dépassez les limites:
   • Attendez quelques minutes
   • Désactivez l'évaluation Magistral
   • Espacez vos requêtes de 10-20 secondes
   • Considérez un upgrade de plan si usage régulier
    """)

if __name__ == "__main__":
    main()
