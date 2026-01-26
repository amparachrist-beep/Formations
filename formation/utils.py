import requests
from django.conf import settings
from django.core.mail import send_mail
from decimal import Decimal


def creer_paiement_moneroo(commande):
    '''
    Initialise un paiement avec Moneroo et retourne l'URL de paiement
    '''
    headers = {
        'Authorization': f'Bearer {settings.MONEROO_API_KEY}',
        'Content-Type': 'application/json',
    }

    # Préparer les données de paiement
    payload = {
        'amount': float(commande.montant_total),
        'currency': 'XAF',  # FCFA
        'description': f'Achat de formation(s) - Commande #{commande.id}',
        'customer': {
            'email': commande.client.email,
            'phone': commande.client.whatsapp,
            'name': commande.client.nom_complet,
        },
        'return_url': f'{settings.SITE_URL}/paiement/callback/{commande.id}/',
        'metadata': {
            'commande_id': commande.id,
            'client_id': commande.client.id,
        }
    }

    try:
        response = requests.post(
            settings.MONEROO_API_URL,
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        # Sauvegarder les informations de la transaction
        commande.moneroo_transaction_id = data.get('transaction_id')
        commande.moneroo_payment_url = data.get('checkout_url')
        commande.save()

        return data.get('checkout_url')

    except requests.exceptions.RequestException as e:
        # Logger l'erreur en production
        print(f"Erreur Moneroo: {e}")
        return None


def verifier_paiement_moneroo(transaction_id):
    '''
    Vérifie le statut d'un paiement auprès de Moneroo
    Retourne True si le paiement est validé
    '''
    headers = {
        'Authorization': f'Bearer {settings.MONEROO_API_KEY}',
    }

    url = f'https://api.moneroo.io/v1/payments/{transaction_id}'

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Vérifier si le paiement est réussi
        return data.get('status') == 'success'

    except requests.exceptions.RequestException as e:
        print(f"Erreur vérification Moneroo: {e}")
        return False


def generer_message_whatsapp(commande):
    '''
    Génère le message WhatsApp pré-rempli après paiement
    '''
    formations_liste = ', '.join([f.titre for f in commande.formations.all()])

    message = (
        f"Bonjour, je viens d'effectuer le paiement pour la/les formation(s) : "
        f"{formations_liste}. "
        f"Commande #{commande.id}. "
        f"Merci de m'envoyer les accès."
    )

    # Encoder le message pour l'URL
    import urllib.parse
    message_encode = urllib.parse.quote(message)

    whatsapp_url = f"https://wa.me/{settings.ADMIN_WHATSAPP.replace('+', '')}?text={message_encode}"

    return whatsapp_url


def envoyer_acces_formation_email(commande):
    '''
    Envoie automatiquement les accès aux formations par email
    Retourne True si l'envoi a réussi, False sinon
    '''
    formations_liste = commande.formations.all()

    # Construction du message HTML
    message_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0;">🎉 Bienvenue !</h1>
            </div>

            <div style="background: white; padding: 30px; border: 1px solid #eee; border-top: none;">
                <p style="font-size: 16px;">Bonjour <strong>{commande.client.nom_complet}</strong>,</p>

                <p>Merci pour votre achat ! Votre paiement a été confirmé avec succès.</p>

                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <p style="margin: 0; font-size: 14px; color: #666;">Numéro de commande</p>
                    <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: #667eea;">#{commande.id}</p>
                    <p style="margin: 10px 0 0 0; font-size: 14px; color: #666;">Montant payé : <strong>{commande.montant_total} FCFA</strong></p>
                </div>

                <h2 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px;">📚 Vos accès aux formations</h2>
    """

    # Ajouter chaque formation
    for formation in formations_liste:
        message_html += f"""
                <div style="border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; background: #f8f9fa; border-radius: 0 8px 8px 0;">
                    <h3 style="color: #2c3e50; margin: 0 0 15px 0; font-size: 18px;">{formation.titre}</h3>
        """

        if formation.lien_youtube:
            message_html += f"""
                    <div style="margin: 10px 0;">
                        <p style="margin: 0; font-weight: bold; color: #555;">🎥 Vidéos de formation (YouTube)</p>
                        <a href="{formation.lien_youtube}" style="color: #667eea; text-decoration: none; word-break: break-all;">{formation.lien_youtube}</a>
                    </div>
            """

        if formation.lien_drive:
            message_html += f"""
                    <div style="margin: 10px 0;">
                        <p style="margin: 0; font-weight: bold; color: #555;">📁 Documents et ressources (Google Drive)</p>
                        <a href="{formation.lien_drive}" style="color: #667eea; text-decoration: none; word-break: break-all;">{formation.lien_drive}</a>
                    </div>
            """

        if not formation.lien_youtube and not formation.lien_drive:
            message_html += f"""
                    <p style="color: #f39c12; margin: 0;">⏳ Les accès seront ajoutés très prochainement</p>
            """

        message_html += """
                </div>
        """

    # Pied du message
    message_html += f"""
                <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 20px; border-radius: 8px; margin: 30px 0;">
                    <h3 style="color: #2c3e50; margin: 0 0 15px 0;">✅ Vos garanties</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li style="margin: 8px 0;">Accès illimité à vie aux ressources</li>
                        <li style="margin: 8px 0;">Support disponible via WhatsApp</li>
                        <li style="margin: 8px 0;">Mises à jour gratuites du contenu</li>
                        <li style="margin: 8px 0;">Certificat de fin de formation</li>
                    </ul>
                </div>

                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; color: #856404;">
                        <strong>💡 Besoin d'aide ?</strong><br>
                        Contactez-nous sur WhatsApp au <strong>{settings.ADMIN_WHATSAPP}</strong>
                    </p>
                </div>

                <p style="margin-top: 30px;">Bonne formation ! 🚀</p>
                <p style="color: #667eea; font-weight: bold;">L'équipe Formations</p>
            </div>

            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px;">
                <p style="margin: 0; font-size: 12px; color: #999;">
                    Cet email a été envoyé automatiquement. Merci de ne pas y répondre.<br>
                    Pour toute question, contactez-nous sur WhatsApp.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    # Message texte simple (fallback pour clients email sans HTML)
    message_text = f"""
🎉 BIENVENUE DANS VOTRE FORMATION !

Bonjour {commande.client.nom_complet},

Merci pour votre achat ! Votre paiement a été confirmé avec succès.

📋 DÉTAILS DE VOTRE COMMANDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Numéro de commande : #{commande.id}
Montant payé : {commande.montant_total} FCFA


📚 VOS ACCÈS AUX FORMATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    for formation in formations_liste:
        message_text += f"\n▶ {formation.titre}\n"
        if formation.lien_youtube:
            message_text += f"  🎥 YouTube : {formation.lien_youtube}\n"
        if formation.lien_drive:
            message_text += f"  📁 Drive : {formation.lien_drive}\n"
        if not formation.lien_youtube and not formation.lien_drive:
            message_text += f"  ⏳ Accès en cours de préparation\n"

    message_text += f"""

✅ VOS GARANTIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Accès illimité à vie
- Support WhatsApp
- Mises à jour gratuites
- Certificat de formation


💡 BESOIN D'AIDE ?
━━━━━━━━━━━━━━━━━━━━━━━━━━━
WhatsApp : {settings.ADMIN_WHATSAPP}


Bonne formation ! 🚀
L'équipe Formations
"""

    try:
        # Envoi de l'email
        send_mail(
            subject=f'🎓 Vos accès aux formations - Commande #{commande.id}',
            message=message_text,  # Version texte
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[commande.client.email],
            html_message=message_html,  # Version HTML (plus jolie)
            fail_silently=False,
        )
        print(f"✅ Email envoyé avec succès à {commande.client.email}")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email : {e}")
        return False