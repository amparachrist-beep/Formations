import requests
import json

# Vos identifiants
API_KEY_COMPLETE = "pvk_sandbox_q4qo8s|01KGDJQP22D5B1Y25ZJK52WC8K"
MERCHANT_ID = "01KFVTY7VAF91HN35A3M2V8TFT"

# Différentes variantes à tester
variantes = {
    "Format complet": API_KEY_COMPLETE,
    "Partie avant pipe": API_KEY_COMPLETE.split('|')[0],
    "Partie après pipe": API_KEY_COMPLETE.split('|')[1],
    "Sans pipe (concaténé)": API_KEY_COMPLETE.replace('|', ''),
}

# Endpoint simple pour tester l'auth
test_url = "https://api.moneroo.io/merchants/" + MERCHANT_ID

print("=" * 70)
print("TEST D'AUTHENTIFICATION MONEROO")
print("=" * 70)

for nom, cle in variantes.items():
    print(f"\n🧪 Test avec : {nom}")
    print(f"   Clé utilisée : {cle[:30]}...")

    headers = {
        "Authorization": f"Bearer {cle}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(test_url, headers=headers, timeout=10)

        print(f"   ✅ Status Code : {response.status_code}")

        if response.status_code == 200:
            print(f"   🎉 SUCCÈS ! Cette clé fonctionne !")
            print(f"   Réponse : {response.json()}")
            break
        elif response.status_code == 401:
            print(f"   ❌ 401 Unauthenticated")
            error = response.json()
            print(f"   Message : {error.get('message', 'N/A')}")
        else:
            print(f"   ⚠️  Réponse : {response.text[:200]}")

    except Exception as e:
        print(f"   ❌ Erreur : {e}")

print("\n" + "=" * 70)
print("TEST TERMINÉ")
print("=" * 70)

# Test supplémentaire : vérifier si Moneroo nécessite un header spécial
print("\n🔍 Test avec headers alternatifs...")

headers_alternatifs = [
    {"X-API-Key": API_KEY_COMPLETE, "Accept": "application/json"},
    {"Api-Key": API_KEY_COMPLETE, "Accept": "application/json"},
    {"Moneroo-API-Key": API_KEY_COMPLETE, "Accept": "application/json"},
]

for i, headers in enumerate(headers_alternatifs, 1):
    print(f"\n   Test {i} : {list(headers.keys())[0]}")
    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"   Status : {response.status_code}")
        if response.status_code == 200:
            print(f"   🎉 SUCCÈS avec ce format de header !")
            print(f"   Réponse : {response.json()}")
            break
    except Exception as e:
        print(f"   Erreur : {e}")