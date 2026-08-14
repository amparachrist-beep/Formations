"""
Script à exécuter EN LOCAL (une seule fois) pour récupérer un refresh token
permettant à votre application Django d'accéder à Google Drive en votre nom.

Prérequis :
    pip install google-auth-oauthlib

Utilisation :
    1. Placez le fichier JSON téléchargé depuis Google Cloud Console
       dans le même dossier que ce script, et renommez-le "client_secret.json".
    2. Lancez : python get_refresh_token.py
    3. Une page navigateur s'ouvre : connectez-vous avec le compte Google
       propriétaire de vos dossiers Drive, puis acceptez les permissions.
    4. Le script affiche le refresh_token dans le terminal : copiez-le,
       vous en aurez besoin pour la variable d'environnement GOOGLE_REFRESH_TOKEN.
"""

from google_auth_oauthlib.flow import InstalledAppFlow

# Scope nécessaire pour gérer les permissions de partage sur Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

CLIENT_SECRET_FILE = 'client_secret.json'


def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES
    )

    # Lance un petit serveur local temporaire + ouvre le navigateur
    creds = flow.run_local_server(port=0)

    print("\n" + "=" * 60)
    print("✅ Authentification réussie !")
    print("=" * 60)
    print(f"\nCLIENT_ID     : {creds.client_id}")
    print(f"CLIENT_SECRET : {creds.client_secret}")
    print(f"REFRESH_TOKEN : {creds.refresh_token}")
    print("\n" + "=" * 60)
    print("⚠️  Copiez ces 3 valeurs dans vos variables d'environnement Render :")
    print("    GOOGLE_CLIENT_ID")
    print("    GOOGLE_CLIENT_SECRET")
    print("    GOOGLE_REFRESH_TOKEN")
    print("=" * 60)


if __name__ == '__main__':
    main()