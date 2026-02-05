from django.urls import path
from . import views

urlpatterns = [
    # Pages principales
    path('', views.catalogue_view, name='catalogue'),

    # Panier
    path('panier/', views.panier_view, name='panier'),
    path('panier/ajouter/<int:formation_id>/', views.ajouter_panier_view, name='ajouter_panier'),
    path('panier/retirer/<int:formation_id>/', views.retirer_panier_view, name='retirer_panier'),
    path('panier/vider/', views.vider_panier_view, name='vider_panier'),

    # Checkout et paiement
    path('checkout/', views.checkout_view, name='checkout'),
    path('paiement/callback/<int:commande_id>/', views.paiement_callback_view, name='paiement_callback'),
    path('confirmation/', views.confirmation_view, name='confirmation'),

    # Admin temporaire
    path('_create_admin/', views.create_superuser_temp, name='create_admin_temp'),

    # ✅ WEBHOOK MONEROO - LA SEULE ROUTE NÉCESSAIRE
    path('moneroo/webhook/', views.moneroo_webhook, name='moneroo_webhook'),
]