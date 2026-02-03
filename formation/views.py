from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Formation, Client, Commande
from .forms import ClientForm
from .utils import creer_paiement_moneroo, verifier_paiement_moneroo, generer_message_whatsapp,  envoyer_acces_formation_email
from decimal import Decimal


def catalogue_view(request):
    '''
    Affiche toutes les formations actives
    '''
    formations = Formation.objects.filter(active=True)

    # DEBUG
    print(f"DEBUG: {formations.count()} formations actives trouvées")
    for f in formations:
        print(f"  - {f.titre}")

    return render(request, 'formation/catalogue.html', {
        'formations': formations
    })



@require_http_methods(["POST"])
def ajouter_panier_view(request, formation_id):
    '''
    Ajoute une formation au panier (session)
    '''
    formation = get_object_or_404(Formation, id=formation_id, active=True)

    panier = request.session.get('panier', {})

    panier[str(formation.id)] = {
        'titre': formation.titre,
        'prix': str(formation.prix),
    }

    request.session['panier'] = panier
    messages.success(request, f'"{formation.titre}" ajoutée au panier !')

    return redirect('panier')


def panier_view(request):
    '''
    Affiche le contenu du panier
    '''
    panier = request.session.get('panier', {})
    formations_ids = panier.keys()
    formations = Formation.objects.filter(id__in=formations_ids)
    total = sum([f.prix for f in formations])

    return render(request, 'formation/panier.html', {
        'formations': formations,
        'total': total
    })


@require_http_methods(["POST"])
def retirer_panier_view(request, formation_id):
    '''
    Retire une formation du panier
    '''
    panier = request.session.get('panier', {})

    if str(formation_id) in panier:
        formation_titre = panier[str(formation_id)]['titre']
        del panier[str(formation_id)]
        request.session['panier'] = panier
        messages.info(request, f'"{formation_titre}" retirée du panier.')

    return redirect('panier')


def vider_panier_view(request):
    '''
    Vide complètement le panier
    '''
    request.session['panier'] = {}
    messages.info(request, 'Panier vidé.')
    return redirect('panier')


def checkout_view(request):
    '''
    Affiche le formulaire client avant paiement
    '''
    panier = request.session.get('panier', {})

    if not panier:
        messages.warning(request, 'Votre panier est vide.')
        return redirect('catalogue')

    formations_ids = panier.keys()
    formations = Formation.objects.filter(id__in=formations_ids)
    total = sum([f.prix for f in formations])

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client, created = Client.objects.get_or_create(
                email=form.cleaned_data['email'],
                defaults={
                    'nom_complet': form.cleaned_data['nom_complet'],
                    'whatsapp': form.cleaned_data['whatsapp'],
                }
            )

            commande = Commande.objects.create(
                client=client,
                montant_total=total
            )
            commande.formations.set(formations)
            print(f"✅ [CHECKOUT] Commande #{commande.id} créée pour {client.email}. Appel Moneroo imminent.")
            try:
                # On tente d'appeler la fonction de paiement
                payment_url = creer_paiement_moneroo(commande)

                if payment_url:
                    # Succès : on redirige vers Moneroo
                    return redirect(payment_url)
                else:
                    # La fonction a retourné None (erreur déjà loggée dans la fonction)
                    messages.error(request, 'Erreur lors de l\'initialisation du paiement.')
                    commande.delete()

            except Exception as e:
                # CAPTURE CRITIQUE : Toute exception qui arriverait AVANT ou PENDANT l'appel
                print(f"🔴 [ERREUR GLOBALE CAPTUREE DANS checkout_view] : {type(e).__name__} - {e}")
                import traceback
                traceback.print_exc()  # Imprime la pile d'appel complète
                messages.error(request, f'Une erreur interne est survenue: {e}')
                commande.delete()
    else:
        form = ClientForm()

    return render(request, 'formation/checkout.html', {
        'form': form,
        'formations': formations,
        'total': total
    })


def paiement_callback_view(request, commande_id):
    '''
    Callback après redirection depuis Moneroo
    Vérifie le paiement et affiche la confirmation
    '''
    commande = get_object_or_404(Commande, id=commande_id)

    # Vérifier le paiement auprès de Moneroo (SÉCURITÉ CRITIQUE)
    if commande.moneroo_transaction_id:
        paiement_valide = verifier_paiement_moneroo(commande.moneroo_transaction_id)

        if paiement_valide and commande.statut == 'en_attente':
            # Marquer la commande comme payée
            commande.marquer_comme_paye()

            # 🆕 ENVOI AUTOMATIQUE DES ACCÈS PAR EMAIL
            email_envoye = envoyer_acces_formation_email(commande)

            if email_envoye:
                # Marquer les accès comme envoyés
                commande.marquer_acces_envoye()
                messages.success(request, '✅ Vos accès ont été envoyés par email !')
            else:
                messages.warning(request, '⚠️ Paiement confirmé. Les accès seront envoyés sous peu.')

            # Vider le panier
            request.session['panier'] = {}

            # Générer le lien WhatsApp
            whatsapp_url = generer_message_whatsapp(commande)

            return render(request, 'formation/paiement_reussi.html', {
                'commande': commande,
                'whatsapp_url': whatsapp_url,
                'email_envoye': email_envoye
            })

    # Si le paiement n'est pas validé
    messages.error(request, 'Le paiement n\'a pas pu être validé.')
    return redirect('catalogue')


def confirmation_view(request):
    '''
    Page de confirmation générique
    '''
    return render(request, 'formation/confirmation.html')


# === TEMPORAIRE : Création superuser ===
import os
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def create_superuser_temp(request):
    """Vue temporaire pour créer un superuser"""
    # Vérifier si déjà créé
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse("""
            <h2>Superuser existe déjà</h2>
            <p><a href="/admin/">Aller à l'admin</a></p>
        """)

    # Créer le superuser
    try:
        User.objects.create_superuser(
            username='admin',
            email='nkouampafranck49@gmail.com',
            password='Admin123!'
        )
        return HttpResponse("""
            <h2>Superuser créé avec succès !</h2>
            <p><strong>Identifiants :</strong></p>
            <ul>
                <li>Username: <strong>admin</strong></li>
                <li>Email: nkouampafranck49@gmail.com</li>
                <li>Password: <strong>Admin123!</strong></li>
            </ul>
            <p><a href="/admin/" style="color: blue; font-weight: bold;">Cliquez ici pour aller à l'admin</a></p>
            <p><strong>⚠️ IMPORTANT :</strong> Retirez cette vue après utilisation !</p>
        """)
    except Exception as e:
        return HttpResponse(f"Erreur : {str(e)}")




# Ajoutez ces imports en haut de votre views.py si nécessaire
import json
import hashlib
import hmac
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt  # Cette décoration est CRUCIALE pour accepter les requêtes POST externes
def pawapay_deposit_webhook(request):
    """
    Gère les notifications de paiement entrant (Deposits) de PawaPay.
    """
    if request.method != 'POST':
        return HttpResponse('Méthode non autorisée', status=405)

    # 1. VALIDATION DE LA SIGNATURE (SÉCURITÉ IMPÉRATIVE)
    # Récupérez la signature envoyée par PawaPay
    received_signature = request.headers.get('X-PawaPay-Signature', '')
    # Récupérez le corps brut de la requête
    payload_body = request.body

    # 🔐 Générer la signature attendue avec votre Webhook Secret
    # NOTE : Vous devez définir cette clé secrète dans vos variables d'environnement
    # (ex: PAWAPAY_WEBHOOK_SECRET) et dans les paramètres de votre app sur Render.
    webhook_secret = settings.PAWAPAY_WEBHOOK_SECRET.encode('utf-8')
    expected_signature = hmac.new(webhook_secret, payload_body, hashlib.sha256).hexdigest()

    # Comparez les signatures de manière sécurisée
    if not hmac.compare_digest(expected_signature, received_signature):
        # La requête ne vient pas de PawaPay, rejetez-la.
        return HttpResponseForbidden('Signature invalide : Webhook non authentifié.')

    # 2. TRAITEMENT DE LA NOTIFICATION
    try:
        payload = json.loads(payload_body.decode('utf-8'))
        # Extrayez les informations critiques (structure à confirmer dans la doc PawaPay)
        transaction_id = payload.get('transactionId')
        status = payload.get('status')  # Par exemple: "COMPLETED", "FAILED"
        amount = payload.get('amount')
        currency = payload.get('currency')

        # ICI, INSÉREZ VOTRE LOGIQUE MÉTIER :
        # - Trouver la commande correspondante (peut-être via une référence dans `payload.get('merchantReference')`)
        # - Mettre à jour son statut de paiement dans votre base de données
        # - Notifier l'utilisateur si nécessaire
        # - Déclencher la livraison de la formation si le paiement est réussi

        print(f"[Webhook PawaPay] Transaction {transaction_id} : Statut = {status}")  # À remplacer par de vrais logs

        # 3. RÉPONSE POSITIVE
        return HttpResponse('Webhook traité avec succès', status=200)

    except json.JSONDecodeError:
        return HttpResponse('Données JSON invalides', status=400)
    except Exception as e:
        # Loggez l'erreur pour investigation
        print(f"Erreur lors du traitement du webhook : {e}")
        return HttpResponse('Erreur interne du serveur', status=500)

# Vous pouvez créer des vues similaires pour `pawapay_payout_webhook` et `pawapay_refund_webhook`
# ou utiliser une vue générique au début.


@csrf_exempt
def pawapay_payout_webhook(request):
    """
    Gère les notifications de paiement sortant (Payouts) de PawaPay.
    (Ex: statut d'un virement que vous avez initié vers un client)
    """
    if request.method != 'POST':
        return HttpResponse('Méthode non autorisée', status=405)

    # 1. VALIDATION DE LA SIGNATURE (identique à la vue des dépôts)
    received_signature = request.headers.get('X-PawaPay-Signature', '')
    payload_body = request.body
    webhook_secret = settings.PAWAPAY_WEBHOOK_SECRET.encode('utf-8')
    expected_signature = hmac.new(webhook_secret, payload_body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, received_signature):
        return HttpResponseForbidden('Signature invalide : Webhook non authentifié.')

    # 2. TRAITEMENT SPÉCIFIQUE AUX PAIEMENTS SORTANTS
    try:
        payload = json.loads(payload_body.decode('utf-8'))
        # Extrayez les informations (structure à vérifier dans la doc PawaPay)
        payout_id = payload.get('payoutId')  # ou 'transactionId'
        status = payload.get('status')  # Ex: "PAID_OUT", "FAILED", "REVERSED"
        amount = payload.get('amount')
        recipient = payload.get('recipient')  # Peut contenir le numéro de téléphone

        # ICI, INSÉREZ VOTRE LOGIQUE MÉTIER :
        # - Trouver le virement correspondant dans votre base de données (via `payout_id` ou une référence interne)
        # - Mettre à jour son statut ("réussi", "échoué", "annulé")
        # - Notifier l'administrateur ou le bénéficiaire en cas d'échec
        # - Mettre à jour le solde du compte si nécessaire

        print(f"[Webhook PawaPay Payout] Payout {payout_id} : Statut = {status}")

        return HttpResponse('Webhook Payout traité', status=200)

    except json.JSONDecodeError:
        return HttpResponse('Données JSON invalides', status=400)
    except Exception as e:
        print(f"Erreur lors du traitement du webhook Payout : {e}")
        return HttpResponse('Erreur interne du serveur', status=500)


@csrf_exempt
def pawapay_refund_webhook(request):
    """
    Gère les notifications de remboursement (Refunds) de PawaPay.
    (Ex: statut d'un remboursement que vous avez initié sur un paiement)
    """
    if request.method != 'POST':
        return HttpResponse('Méthode non autorisée', status=405)

    # 1. VALIDATION DE LA SIGNATURE (identique)
    received_signature = request.headers.get('X-PawaPay-Signature', '')
    payload_body = request.body
    webhook_secret = settings.PAWAPAY_WEBHOOK_SECRET.encode('utf-8')
    expected_signature = hmac.new(webhook_secret, payload_body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, received_signature):
        return HttpResponseForbidden('Signature invalide : Webhook non authentifié.')

    # 2. TRAITEMENT SPÉCIFIQUE AUX REMBOURSEMENTS
    try:
        payload = json.loads(payload_body.decode('utf-8'))
        # Extrayez les informations (structure à vérifier dans la doc PawaPay)
        refund_id = payload.get('refundId')
        original_transaction_id = payload.get('originalTransactionId')  # L'ID du paiement initial
        status = payload.get('status')  # Ex: "REFUNDED", "FAILED"
        amount = payload.get('amount')

        # ICI, INSÉREZ VOTRE LOGIQUE MÉTIER :
        # - Trouver la commande et le paiement original dans votre base de données
        # - Mettre à jour le statut du remboursement
        # - Si le remboursement est réussi, marquer la commande comme "remboursée" et potentiellement réattribuer l'accès à la formation
        # - Notifier le client

        print(f"[Webhook PawaPay Refund] Remboursement {refund_id} pour transaction {original_transaction_id} : Statut = {status}")

        return HttpResponse('Webhook Refund traité', status=200)

    except json.JSONDecodeError:
        return HttpResponse('Données JSON invalides', status=400)
    except Exception as e:
        print(f"Erreur lors du traitement du webhook Refund : {e}")
        return HttpResponse('Erreur interne du serveur', status=500)


# Dans votre views.py
import json
import hashlib
import hmac
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt  # Essentiel car la requête vient de l'extérieur
def moneroo_webhook_handler(request):
    """
    Gère les notifications de webhook envoyées par Moneroo.
    """
    if request.method != 'POST':
        return HttpResponse('Méthode non autorisée', status=405)

    # 1. OPTIONNEL MAIS FORTEMENT RECOMMANDÉ : Valider la signature
    # Moneroo signe ses webhooks. Vérifiez la présence d'un header comme 'X-Moneroo-Signature'
    received_signature = request.headers.get('X-Moneroo-Signature', '')
    payload_body = request.body

    # Vous devez configurer un secret de webhook dans votre tableau de bord Moneroo
    # et le sauvegarder dans vos variables d'environnement (ex: MONEROO_WEBHOOK_SECRET)
    webhook_secret = settings.MONEROO_WEBHOOK_SECRET.encode('utf-8')
    expected_signature = hmac.new(webhook_secret, payload_body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, received_signature):
        return HttpResponseForbidden('Signature de webhook invalide.')

    # 2. Traiter la charge utile (payload) JSON
    try:
        payload = json.loads(payload_body.decode('utf-8'))
        # Extrayez les informations critiques. La structure exacte dépend de Moneroo.
        # Voici un exemple basé sur des webhooks de paiement courants :
        event_type = payload.get('type')  # Ex: 'payment.succeeded'
        payment_id = payload.get('data', {}).get('id')
        status = payload.get('data', {}).get('status')
        amount = payload.get('data', {}).get('amount')
        customer_email = payload.get('data', {}).get('customer_email')

        print(f"[Webhook Moneroo] Événement : {event_type}, Paiement ID: {payment_id}, Statut: {status}")

        # 3. INSÉREZ VOTRE LOGIQUE MÉTIER ICI :
        # - Trouvez la commande correspondante dans votre base de données (via payment_id ou une référence).
        # - Mettez à jour son statut (ex: 'payé', 'échoué', 'remboursé').
        # - Si le paiement est confirmé, activez l'accès à la formation pour l'utilisateur.
        # - Envoyez un email de confirmation au client.

        # 4. Répondre rapidement pour confirmer la réception
        return HttpResponse('Webhook reçu avec succès', status=200)

    except json.JSONDecodeError:
        return HttpResponse('Données JSON invalides', status=400)
    except Exception as e:
        # Loggez l'erreur complète pour le débogage
        print(f"Erreur lors du traitement du webhook Moneroo: {e}")
        # Il est important de renvoyer un code 2xx même en cas d'erreur de traitement,
        # pour éviter que Moneroo ne réessaie trop souvent. Loggez l'erreur côté serveur.
        return HttpResponse('Webhook traité (erreur loggée)', status=200)


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Commande

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Commande
import hmac
import hashlib


@csrf_exempt
def moneroo_webhook(request):
    """
    Webhook Moneroo - Compatible Sandbox (sans secret) et Production (avec secret)
    """
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    # --- Lecture du body brut ---
    raw_body = request.body
    print("🔔 WEBHOOK MONEROO REÇU")
    print("=" * 60)

    # --- VALIDATION DE SIGNATURE (uniquement si secret configuré) ---
    webhook_secret = getattr(settings, 'MONEROO_WEBHOOK_SECRET', '')

    if webhook_secret:
        # Mode PRODUCTION : Validation obligatoire
        received_signature = request.headers.get('X-Moneroo-Signature', '')

        if not received_signature:
            print("⚠️  Pas de signature X-Moneroo-Signature")
            return JsonResponse({"error": "Signature manquante"}, status=401)

        # Calculer la signature attendue
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            raw_body,
            hashlib.sha256
        ).hexdigest()

        # Comparer de manière sécurisée
        if not hmac.compare_digest(expected_signature, received_signature):
            print("🔴 SIGNATURE INVALIDE !")
            print(f"   Reçue    : {received_signature[:20]}...")
            print(f"   Attendue : {expected_signature[:20]}...")
            return JsonResponse({"error": "Signature invalide"}, status=403)

        print("✅ Signature validée")
    else:
        # Mode SANDBOX : Pas de validation (pour les tests)
        print("⚠️  Mode SANDBOX : Validation de signature désactivée")

    # --- Parse JSON ---
    try:
        payload = json.loads(raw_body.decode('utf-8'))
        print(f"📦 Payload : {json.dumps(payload, indent=2)}")
    except json.JSONDecodeError as e:
        print(f"❌ ERREUR JSON : {e}")
        return JsonResponse({"error": "JSON invalide"}, status=400)

    # --- Extraction des données ---
    # Structure possible de Moneroo :
    # {
    #   "event": "payment.success",
    #   "data": {
    #     "id": "py_xxx",
    #     "status": "success",
    #     "amount": 2500,
    #     ...
    #   },
    #   "metadata": {
    #     "commande_id": "30"
    #   }
    # }

    event_type = payload.get("event", "")
    payment_data = payload.get("data", {})
    metadata = payment_data.get("metadata") or payload.get("metadata", {})

    # Récupérer l'ID de commande
    commande_id = (
            metadata.get("commande_id") or
            metadata.get("commandeId") or
            payload.get("commande_id")
    )

    # Récupérer le statut
    status = (
            payment_data.get("status", "") or
            payload.get("status", "")
    ).lower()

    print(f"📋 Type événement : {event_type}")
    print(f"📋 Statut paiement : {status}")
    print(f"📋 Commande ID : {commande_id}")

    if not commande_id:
        print("❌ ERREUR : commande_id manquant dans le webhook")
        return JsonResponse({"error": "commande_id manquant"}, status=400)

    # --- Récupération de la commande ---
    try:
        commande = Commande.objects.get(id=commande_id)
        print(f"✅ Commande #{commande.id} trouvée - Statut actuel: {commande.statut}")
    except Commande.DoesNotExist:
        print(f"❌ Commande #{commande_id} introuvable")
        return JsonResponse({"error": "Commande introuvable"}, status=404)

    # --- Vérification des doublons ---
    if commande.statut == 'paye' and status in ["success", "paid", "completed", "successful"]:
        print(f"⚠️  Commande #{commande.id} déjà PAYÉE - Webhook ignoré (doublon)")
        return JsonResponse({"message": "Paiement déjà traité"}, status=200)

    # --- Mise à jour du statut ---
    if status in ["success", "paid", "completed", "successful"]:
        # PAIEMENT RÉUSSI
        commande.marquer_comme_paye()
        print(f"✅ Commande #{commande.id} marquée comme PAYÉE")

        # Optionnel : Envoyer les accès par email
        from .utils import envoyer_acces_formation_email
        email_envoye = envoyer_acces_formation_email(commande)

        if email_envoye:
            commande.marquer_acces_envoye()
            print(f"✅ Email d'accès envoyé à {commande.client.email}")

        return JsonResponse({
            "message": "Paiement confirmé",
            "commande_id": commande.id,
            "email_envoye": email_envoye
        }, status=200)

    elif status in ["failed", "cancelled", "canceled", "declined"]:
        # PAIEMENT ÉCHOUÉ
        commande.statut = 'annule'
        commande.save()
        print(f"❌ Commande #{commande.id} marquée comme ANNULÉE")
        return JsonResponse({"message": "Paiement échoué"}, status=200)

    else:
        # STATUT INCONNU OU EN ATTENTE
        print(f"ℹ️  Statut ignoré pour commande #{commande.id} : {status}")
        return JsonResponse({"message": f"Statut ignoré: {status}"}, status=200)