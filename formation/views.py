from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Formation, Client, Commande
from .forms import ClientForm
from .utils import generer_message_whatsapp, envoyer_acces_formation_email
import urllib.parse
from django.core.paginator import Paginator
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
import json
import logging
import requests
from .services.senepay import senepay

# ==================== CATALOGUE ====================

def catalogue_view(request):
    """Affiche toutes les formations actives"""
    formations = Formation.objects.filter(active=True).order_by('date_creation')
    paginator = Paginator(formations, 3)  # 👈 5 formations par page
    page_number = request.GET.get('page')
    formations = paginator.get_page(page_number)
    return render(request, 'formation/catalogue.html', {'formations': formations})


# ==================== PANIER ====================

@require_http_methods(["POST"])
def ajouter_panier_view(request, formation_id):
    """Ajoute une formation au panier (session)"""
    formation = get_object_or_404(Formation, id=formation_id, active=True)
    panier = request.session.get('panier', {})
    panier[str(formation.id)] = {
        'titre': formation.titre,
        'prix': str(formation.prix_actuel),
    }
    request.session['panier'] = panier
    messages.success(request, f'"{formation.titre}" ajoutée au panier !')
    return redirect('panier')


def panier_view(request):
    """Affiche le contenu du panier"""
    panier = request.session.get('panier', {})
    formations = Formation.objects.filter(id__in=panier.keys())
    total = sum([f.prix_actuel for f in formations])
    return render(request, 'formation/panier.html', {'formations': formations, 'total': total})


@require_http_methods(["POST"])
def retirer_panier_view(request, formation_id):
    """Retire une formation du panier"""
    panier = request.session.get('panier', {})
    if str(formation_id) in panier:
        titre = panier[str(formation_id)]['titre']
        del panier[str(formation_id)]
        request.session['panier'] = panier
        messages.info(request, f'"{titre}" retirée du panier.')
    return redirect('panier')


def vider_panier_view(request):
    """Vide complètement le panier"""
    request.session['panier'] = {}
    messages.info(request, 'Panier vidé.')
    return redirect('panier')


# ==================== CHECKOUT ====================

def checkout_view(request):
    """Affiche le formulaire client avant paiement"""
    panier = request.session.get('panier', {})
    if not panier:
        messages.warning(request, 'Votre panier est vide.')
        return redirect('catalogue')

    formations = Formation.objects.filter(id__in=panier.keys())
    total = sum([f.prix_actuel for f in formations])

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client, _ = Client.objects.get_or_create(
                email=form.cleaned_data['email'],
                defaults={
                    'nom_complet': form.cleaned_data['nom_complet'],
                    'whatsapp': form.cleaned_data['whatsapp'],
                }
            )
            commande = Commande.objects.create(client=client, montant_total=total)
            commande.formations.set(formations)
            request.session['commande_en_cours'] = commande.id
            print(f"✅ [CHECKOUT] Commande #{commande.id} créée pour {client.email}")
            return redirect('choix_paiement', commande_id=commande.id)
    else:
        form = ClientForm()

    return render(request, 'formation/checkout.html', {
        'form': form,
        'formations': formations,
        'total': total,
    })


# ==================== CHOIX PAIEMENT MOBILE MONEY ====================

# views.py - Version modifiée (sans redemander le téléphone)

def choix_paiement_view(request, commande_id):
    """Page de choix du paiement Mobile Money via SenePay"""
    commande = get_object_or_404(Commande, id=commande_id)

    # Sécurité : vérifier que c'est bien la commande en cours dans la session
    if request.session.get('commande_en_cours') != commande_id:
        messages.error(request, 'Session invalide. Veuillez recommencer.')
        return redirect('catalogue')

    # Vérifier que la commande n'est pas déjà payée
    if commande.statut in ['paye', 'acces_envoye']:
        messages.warning(request, 'Cette commande a déjà été payée.')
        return redirect('confirmation')

    formations = commande.formations.all()

    # Opérateurs supportés par SenePay
    OPERATEURS = [
        {
            'id': 'wave',
            'nom': 'Wave',
            'icon': '🌊',
            'couleur': '#00B4D8',
            'description': 'Paiement instantané'
        },
        {
            'id': 'orange',
            'nom': 'Orange Money',
            'icon': '🟠',
            'couleur': '#FF6600',
            'description': 'Nécessite code OTP'
        },
        {
            'id': 'mtn',
            'nom': 'MTN Mobile Money',
            'icon': '🟡',
            'couleur': '#FFCC00',
            'description': 'Confirmation par USSD'
        },
        {
            'id': 'free',
            'nom': 'Free Money',
            'icon': '🔴',
            'couleur': '#E8192C',
            'description': 'Paiement mobile Free'
        },
    ]

    return render(request, 'formation/choix_paiement.html', {
        'commande': commande,
        'formations': formations,
        'operateurs': OPERATEURS,
        'total': commande.montant_total,
        'client_phone': commande.client.whatsapp,  # ← Numéro déjà existant !
    })


# ==================== CONFIRMATION ====================

def confirmation_view(request):
    """Page de confirmation générique"""
    return render(request, 'formation/confirmation.html')


# ==================== ADMIN TEMPORAIRE ====================

@csrf_exempt
def create_superuser_temp(request):
    """Vue temporaire pour créer un superuser — À RETIRER EN PRODUCTION"""
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
            <h2>✅ Superuser créé avec succès !</h2>
            <ul>
                <li>Username : <strong>admin</strong></li>
                <li>Password : <strong>Admin123!</strong></li>
            </ul>
            <p><a href="/admin/">Aller à l'admin</a></p>
            <p><strong>⚠️ Retirez cette vue après utilisation !</strong></p>
        """)
    except Exception as e:
        return HttpResponse(f"Erreur : {e}")


# views.py

from django.shortcuts import render, get_object_or_404
from .models import Formation


def detail_formation(request, id):
    formation = get_object_or_404(Formation, id=id)

    context = {
        'formation': formation,
    }

    return render(
        request,
        'formation/detail_formation.html',
        context
    )

def achat_direct_view(request, formation_id):
    """Acheter une seule formation directement"""

    formation = get_object_or_404(
        Formation,
        id=formation_id,
        active=True
    )

    # Créer un panier temporaire avec UNE seule formation
    request.session['panier'] = {
        str(formation.id): {
            'titre': formation.titre,
            'prix': str(formation.prix_actuel),
        }
    }

    return redirect('checkout')

def about(request):
    return render(request, 'formation/about.html')


# views.py - AJOUTEZ CES FONCTIONS

from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .services.senepay import senepay
import json
import logging

logger = logging.getLogger(__name__)


def paiement_senepay(request, commande_id):
    """Redirige vers la page de paiement SenePay"""

    commande = get_object_or_404(Commande, id=commande_id)

    # Vérifier que c'est la bonne commande
    if request.session.get('commande_en_cours') != commande_id:
        messages.error(request, 'Session invalide')
        return redirect('catalogue')

    # Éviter double paiement
    if commande.statut in ['paye', 'acces_envoye']:
        messages.warning(request, 'Cette commande est déjà payée')
        return redirect('confirmation')

    # Récupération des données POST (opérateur et téléphone)
    if request.method == 'POST':
        operator = request.POST.get('operator')
        phone = request.POST.get('phone')

        if not operator or not phone:
            messages.error(request, 'Opérateur ou numéro de téléphone manquant')
            return redirect('choix_paiement', commande_id=commande.id)

        # Nettoyer le numéro de téléphone (enlever les espaces, +, etc.)
        phone = ''.join(filter(str.isdigit, phone))

        # Sauvegarde dans la commande
        commande.operateur_paiement = operator
        commande.reference_paiement = phone
        commande.save()
    else:
        # Si pas de POST (accès direct), utiliser les données existantes
        if not commande.reference_paiement:
            messages.error(request, 'Informations de paiement manquantes')
            return redirect('choix_paiement', commande_id=commande.id)
        phone = commande.reference_paiement
        operator = commande.operateur_paiement

    try:
        # Construction des URLs absolues
        site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else request.build_absolute_uri('/').rstrip('/')

        # Création de la session de paiement SenePay
        session = senepay.create_checkout(
            amount=commande.montant_total,
            order_ref=f"CMD-{commande.id}",
            success_url=f"{site_url}{reverse('paiement_succes')}",
            cancel_url=f"{site_url}{reverse('paiement_annule')}",
            webhook_url=f"{site_url}{reverse('senepay_webhook')}"
        )

        # Sauvegarde des informations SenePay
        commande.session_token = session['sessionToken']
        commande.senepay_status = session['status']
        commande.save()

        logger.info(f"Session SenePay créée pour commande #{commande.id}: {session['sessionToken']}")

        # Redirection vers la page de paiement SenePay
        return redirect(session['checkoutUrl'])

    except requests.exceptions.HTTPError as e:
        # Gestion spécifique des erreurs HTTP
        error_msg = ""
        if e.response.status_code == 401:
            error_msg = "Erreur d'authentification SenePay. Vérifiez vos clés API."
        elif e.response.status_code == 403:
            error_msg = "Compte SenePay non validé. Vérifiez votre KYC."
        elif e.response.status_code == 400:
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message', 'Paramètres invalides')
            except:
                error_msg = "Paramètres de paiement invalides"
        else:
            error_msg = f"Erreur SenePay: {str(e)}"

        logger.error(f"Erreur HTTP SenePay: {e.response.status_code} - {error_msg}")
        messages.error(request, error_msg)
        return redirect('choix_paiement', commande_id=commande.id)

    except Exception as e:
        logger.error(f"Erreur SenePay inattendue: {str(e)}")
        messages.error(request, f"Erreur technique: {str(e)}")
        return redirect('panier')

@csrf_exempt
def senepay_webhook(request):
    """Reçoit la confirmation de paiement depuis SenePay"""

    try:
        payload = json.loads(request.body)
    except:
        return HttpResponse("Invalid JSON", status=400)

    logger.info(f"Webhook reçu: {payload}")

    # Paiement réussi
    if payload.get('event') == 'checkout.session.completed':
        session_token = payload.get('sessionToken')
        transaction_id = payload.get('transactionId')

        try:
            commande = Commande.objects.get(session_token=session_token)

            # Marquer comme payée
            commande.statut = 'paye'
            commande.date_paiement = timezone.now()
            commande.senepay_transaction_id = transaction_id
            commande.senepay_status = 'completed'
            commande.save()

            # 🔥 ENVOI DES ACCÈS PAR EMAIL
            from .utils import envoyer_acces_formation_email

            # Préparez les liens
            liens_acces = []
            for formation in commande.formations.all():
                if formation.lien_drive:
                    liens_acces.append({'titre': formation.titre, 'lien': formation.lien_drive})
                elif formation.lien_youtube:
                    liens_acces.append({'titre': formation.titre, 'lien': formation.lien_youtube})

            # Envoi
            envoyer_acces_formation_email(
                email=commande.client.email,
                nom_client=commande.client.nom_complet,
                formations=liens_acces,
                commande_id=commande.id
            )

            # Optionnel: envoyer un message WhatsApp de confirmation
            logger.info(f"✅ Commande #{commande.id} payée avec succès")

        except Commande.DoesNotExist:
            logger.error(f"Commande non trouvée pour token: {session_token}")

    return HttpResponse("OK", status=200)


def paiement_succes(request):
    """Page après paiement réussi"""
    return render(request, 'formation/paiement_succes.html')


def paiement_annule(request):
    """Page après annulation"""
    messages.warning(request, 'Paiement annulé')
    return redirect('catalogue')