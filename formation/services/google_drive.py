"""
formation/services/google_drive.py

Donne automatiquement accès à un dossier Google Drive à un email client,
en s'authentifiant via OAuth2 (refresh token) au nom du propriétaire du compte
Google (vous), plutôt qu'un compte de service (bloqué par la politique
d'organisation iam.disableServiceAccountKeyCreation).
"""

import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_URI = 'https://oauth2.googleapis.com/token'


def _get_credentials():
    """
    Reconstruit des credentials valides à partir du refresh token stocké.
    google-auth régénère automatiquement un access_token à chaque appel
    si besoin (le refresh token, lui, n'expire pas sauf révocation manuelle).
    """
    creds = Credentials(
        token=None,  # pas d'access token en cache, on le régénère à la volée
        refresh_token=settings.GOOGLE_REFRESH_TOKEN,
        token_uri=TOKEN_URI,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def _get_drive_service():
    creds = _get_credentials()
    return build('drive', 'v3', credentials=creds)


def donner_acces_drive(email_client, folder_id):
    """
    Donne l'accès en lecture à un dossier Drive pour un email donné.
    Retourne True si succès, False sinon.
    """
    if not folder_id:
        logger.warning("Pas de folder_id fourni, accès Drive ignoré")
        return False

    try:
        service = _get_drive_service()
        permission = {
            'type': 'user',
            'role': 'reader',
            'emailAddress': email_client,
        }
        service.permissions().create(
            fileId=folder_id,
            body=permission,
            sendNotificationEmail=True,
            fields='id',
        ).execute()
        logger.info(f"✅ Accès Drive accordé à {email_client} pour dossier {folder_id}")
        return True

    except HttpError as e:
        logger.error(f"❌ Erreur Google Drive API pour {email_client} / {folder_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur inattendue Drive: {e}")
        return False