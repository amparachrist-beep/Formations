from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalogue_view, name='catalogue'),
    path('panier/', views.panier_view, name='panier'),
    path('panier/ajouter/<int:formation_id>/', views.ajouter_panier_view, name='ajouter_panier'),
    path('panier/retirer/<int:formation_id>/', views.retirer_panier_view, name='retirer_panier'),
    path('panier/vider/', views.vider_panier_view, name='vider_panier'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('paiement/callback/<int:commande_id>/', views.paiement_callback_view, name='paiement_callback'),
    path('confirmation/', views.confirmation_view, name='confirmation'),
    path('_create_admin/', views.create_superuser_temp, name='create_admin_temp'),

    # --- NOUVELLES ROUTES POUR LES WEBHOOKS PAWAPAY ---
    # Ces chemins doivent CORRESPONDRE exactement aux URLs configurées dans le tableau de bord PawaPay
    path('api/pawapay/webhook/deposit', views.pawapay_deposit_webhook, name='pawapay_deposit'),
    path('api/pawapay/webhook/payout', views.pawapay_payout_webhook, name='pawapay_payout'),
    path('api/pawapay/webhook/refund', views.pawapay_refund_webhook, name='pawapay_refund'),
    path('webhooks/moneroo/', views.moneroo_webhook_handler, name='moneroo_webhook'),
    path("webhooks/moneroo/", views.moneroo_webhook, name="moneroo_webhook")

]