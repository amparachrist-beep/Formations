from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Formation, Client, Commande
from .forms import ClientForm
from .utils import creer_paiement_moneroo, generer_message_whatsapp, envoyer_acces_formation_email
from decimal import Decimal
import json
import hashlib
import hmac


def catalogue_view(request):
    '''Affiche toutes les formations actives'''
    formations = Formation.objects.filter(active=True)
    print(f"DEBUG: {formations.count()} formations actives trouvées")
    for f in formations:
        print(f"  - {f.titre}")
    return render(request, 'formation/catalogue.html', {'formations': formations})


@require_http_methods(["POST"])
def ajouter_panier_view(request, formation_id):
    '''Ajoute une formation au panier (session)'''
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
    '''Affiche le contenu du panier'''
    panier = request.session.get('panier', {})
    formations_ids = panier.keys()
    formations = Formation.objects.filter(id__in=formations_ids)
    total = sum([f.prix for f in formations])
    return render(request, 'formation/panier.html', {'formations': formations, 'total': total})


@require_http_methods(["POST"])
def retirer_panier_view(request, formation_id):
    '''Retire une formation du panier'''
    panier = request.session.get('panier', {})
    if str(formation_id) in panier:
        formation_titre = panier[str(formation_id)]['titre']
        del panier[str(formation_id)]
        request.session['panier'] = panier
        messages.info(request, f'"{formation_titre}" retirée du panier.')
    return redirect('panier')


def vider_panier_view(request):
    '''Vide complètement le panier'''
    request.session['panier'] = {}
    messages.info(request, 'Panier vidé.')
    return redirect('panier')


def checkout_view(request):
    '''Affiche le formulaire client avant paiement'''
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
            commande = Commande.objects.create(client=client, montant_total=total)
            commande.formations.set(formations)
            print(f"✅ [CHECKOUT] Commande #{commande.id} créée pour {client.email}")

            try:
                payment_url = creer_paiement_moneroo(commande)
                if payment_url:
                    return redirect(payment_url)
                else:
                    messages.error(request, 'Erreur lors de l\'initialisation du paiement.')
                    commande.delete()
            except Exception as e:
                print(f"🔴 [ERREUR] {type(e).__name__} - {e}")
                import traceback
                traceback.print_exc()
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
    VERSION AMÉLIORÉE : Gère le cas où le webhook a déjà traité le paiement
    '''
    commande = get_object_or_404(Commande, id=commande_id)

    print("=" * 60)
    print(f"[CALLBACK] Commande #{commande_id}")
    print(f"[CALLBACK] Statut actuel : {commande.statut}")
    print(f"[CALLBACK] Query params : {dict(request.GET)}")
    print("=" * 60)

    # CAS 1 : Le webhook a déjà marqué la commande comme payée
    if commande.statut == 'paye' or commande.statut == 'acces_envoye':
        print(f"✅ [CALLBACK] Commande déjà traitée par webhook - Affichage confirmation")
        messages.success(request, '✅ Paiement confirmé ! Vos accès ont été envoyés par email.')

        # Vider le panier
        request.session['panier'] = {}

        # Générer le lien WhatsApp
        whatsapp_url = generer_message_whatsapp(commande)

        return render(request, 'formation/paiement_reussi.html', {
            'commande': commande,
            'whatsapp_url': whatsapp_url,
            'email_envoye': True
        })

    # CAS 2 : Le paiement n'a pas encore été traité - Traiter maintenant
    # En mode Sandbox, on fait confiance au paramètre paymentStatus de Moneroo
    payment_status = request.GET.get('paymentStatus', '').lower()
    payment_id = request.GET.get('paymentId', '')

    print(f"[CALLBACK] paymentStatus : {payment_status}")
    print(f"[CALLBACK] paymentId : {payment_id}")

    if payment_status in ['success', 'successful', 'paid', 'completed']:
        print(f"✅ [CALLBACK] Paiement confirmé par Moneroo - Traitement")

        # Marquer la commande comme payée
        commande.marquer_comme_paye()

        # Envoyer les accès par email
        email_envoye = envoyer_acces_formation_email(commande)

        if email_envoye:
            commande.marquer_acces_envoye()
            messages.success(request, '✅ Vos accès ont été envoyés par email !')
            print(f"✅ [CALLBACK] Email envoyé à {commande.client.email}")
        else:
            messages.warning(request, '⚠️ Paiement confirmé. Les accès seront envoyés sous peu.')
            print(f"⚠️  [CALLBACK] Échec envoi email")

        # Vider le panier
        request.session['panier'] = {}

        # Générer le lien WhatsApp
        whatsapp_url = generer_message_whatsapp(commande)

        return render(request, 'formation/paiement_reussi.html', {
            'commande': commande,
            'whatsapp_url': whatsapp_url,
            'email_envoye': email_envoye
        })

    # CAS 3 : Paiement échoué ou annulé
    elif payment_status in ['failed', 'cancelled', 'canceled', 'declined']:
        print(f"❌ [CALLBACK] Paiement échoué : {payment_status}")
        commande.statut = 'annule'
        commande.save()
        messages.error(request, 'Le paiement a été annulé ou a échoué.')
        return redirect('catalogue')

    # CAS 4 : Statut inconnu ou pas de paymentStatus
    else:
        print(f"⚠️  [CALLBACK] Statut inconnu ou manquant : {payment_status}")
        messages.warning(request, 'Le paiement est en cours de traitement. Veuillez patienter quelques instants.')
        return redirect('catalogue')


def confirmation_view(request):
    '''Page de confirmation générique'''
    return render(request, 'formation/confirmation.html')


@csrf_exempt
def create_superuser_temp(request):
    """Vue temporaire pour créer un superuser"""
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse("""
            <h2>Superuser existe déjà</h2>
            <p><a href="/admin/">Aller à l'admin</a></p>
        """)

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
            <p><a href="/admin/" style="color: blue; font-weight: bold;">Aller à l'admin</a></p>
            <p><strong>⚠️ IMPORTANT :</strong> Retirez cette vue après utilisation !</p>
        """)
    except Exception as e:
        return HttpResponse(f"Erreur : {str(e)}")


@csrf_exempt
def moneroo_webhook(request):
    """
    Webhook Moneroo - Compatible Sandbox (sans secret) et Production (avec secret)
    """
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    raw_body = request.body
    print("🔔 WEBHOOK MONEROO REÇU")
    print("=" * 60)

    # Validation de signature (uniquement si secret configuré)
    webhook_secret = getattr(settings, 'MONEROO_WEBHOOK_SECRET', '')

    if webhook_secret:
        received_signature = request.headers.get('X-Moneroo-Signature', '')
        if not received_signature:
            print("⚠️  Pas de signature X-Moneroo-Signature")
            return JsonResponse({"error": "Signature manquante"}, status=401)

        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            raw_body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, received_signature):
            print("🔴 SIGNATURE INVALIDE !")
            return JsonResponse({"error": "Signature invalide"}, status=403)

        print("✅ Signature validée")
    else:
        print("⚠️  Mode SANDBOX : Validation de signature désactivée")

    # Parse JSON
    try:
        payload = json.loads(raw_body.decode('utf-8'))
        print(f"📦 Payload : {json.dumps(payload, indent=2)}")
    except json.JSONDecodeError as e:
        print(f"❌ ERREUR JSON : {e}")
        return JsonResponse({"error": "JSON invalide"}, status=400)

    # Extraction des données
    event_type = payload.get("event", "")
    payment_data = payload.get("data", {})
    metadata = payment_data.get("metadata") or payload.get("metadata", {})

    commande_id = (
            metadata.get("commande_id") or
            metadata.get("commandeId") or
            payload.get("commande_id")
    )

    status = (
            payment_data.get("status", "") or
            payload.get("status", "")
    ).lower()

    print(f"📋 Type événement : {event_type}")
    print(f"📋 Statut paiement : {status}")
    print(f"📋 Commande ID : {commande_id}")

    if not commande_id:
        print("❌ ERREUR : commande_id manquant")
        return JsonResponse({"error": "commande_id manquant"}, status=400)

    # Récupération de la commande
    try:
        commande = Commande.objects.get(id=commande_id)
        print(f"✅ Commande #{commande.id} trouvée - Statut: {commande.statut}")
    except Commande.DoesNotExist:
        print(f"❌ Commande #{commande_id} introuvable")
        return JsonResponse({"error": "Commande introuvable"}, status=404)

    # Vérification des doublons
    if commande.statut == 'paye' and status in ["success", "paid", "completed", "successful"]:
        print(f"⚠️  Commande déjà PAYÉE - Webhook ignoré")
        return JsonResponse({"message": "Paiement déjà traité"}, status=200)

    # Mise à jour du statut
    if status in ["success", "paid", "completed", "successful"]:
        commande.marquer_comme_paye()
        print(f"✅ Commande #{commande.id} marquée comme PAYÉE")

        email_envoye = envoyer_acces_formation_email(commande)
        if email_envoye:
            commande.marquer_acces_envoye()
            print(f"✅ Email envoyé à {commande.client.email}")

        return JsonResponse({
            "message": "Paiement confirmé",
            "commande_id": commande.id,
            "email_envoye": email_envoye
        }, status=200)

    elif status in ["failed", "cancelled", "canceled", "declined"]:
        commande.statut = 'annule'
        commande.save()
        print(f"❌ Commande #{commande.id} ANNULÉE")
        return JsonResponse({"message": "Paiement échoué"}, status=200)

    else:
        print(f"ℹ️  Statut ignoré : {status}")
        return JsonResponse({"message": f"Statut ignoré: {status}"}, status=200)