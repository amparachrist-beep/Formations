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

def choix_paiement_view(request, commande_id):
    """Page de choix du mode de paiement Mobile Money via WhatsApp"""
    commande = get_object_or_404(Commande, id=commande_id)

    # Sécurité : vérifier que c'est bien la commande en cours dans la session
    if request.session.get('commande_en_cours') != commande_id:
        messages.error(request, 'Session invalide. Veuillez recommencer.')
        return redirect('catalogue')

    formations = commande.formations.all()
    noms_formations = ', '.join([f.titre for f in formations])

    # Message pré-rempli envoyé sur WhatsApp
    message = (
        f"Bonjour ! Je souhaite régler ma commande n°{commande.id}.\n"
        f"🎓 Formation(s) : {noms_formations}\n"
        f"💰 Montant : {commande.montant_total} FCFA\n"
        f"👤 Nom : {commande.client.nom_complet}\n"
        f"📧 Email : {commande.client.email}\n"
        f"Je vous envoie ma preuve de paiement."
    )
    message_encode = urllib.parse.quote(message)

    OPERATEURS = [
        {
            'id': 'airtel',
            'nom': 'Airtel Money',
            'numero_display': '05 334 40 85',
            'numero_whatsapp': '242053344085',
            'couleur': '#E8192C',
            'logo_emoji': '🔴',
        },
        {
            'id': 'mtn',
            'nom': 'Mobile Money (MTN)',
            'numero_display': '06 181 42 79',
            'numero_whatsapp': '242061814279',
            'couleur': '#FFCC00',
            'logo_emoji': '🟡',
        },
        {
            'id': 'orange',
            'nom': 'Orange Money',
            'numero_display': '+221 78 178 33 02',
            'numero_whatsapp': '221781783302',
            'couleur': '#FF6600',
            'logo_emoji': '🟠',
        },
    ]

    # Ajouter le lien WhatsApp à chaque opérateur
    for op in OPERATEURS:
        op['whatsapp_url'] = f"https://wa.me/{op['numero_whatsapp']}?text={message_encode}"

    return render(request, 'formation/choix_paiement.html', {
        'commande': commande,
        'formations': formations,
        'operateurs': OPERATEURS,
        'total': commande.montant_total,
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
    return render(request, 'formations/about.html')