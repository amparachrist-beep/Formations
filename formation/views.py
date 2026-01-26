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


def detail_formation_view(request, formation_id):
    '''
    Affiche le détail d'une formation
    '''
    formation = get_object_or_404(Formation, id=formation_id, active=True)
    return render(request, 'formation/detail_formation.html', {
        'formation': formation
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

            payment_url = creer_paiement_moneroo(commande)

            if payment_url:
                return redirect(payment_url)
            else:
                messages.error(request, 'Erreur lors de l\'initialisation du paiement.')
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