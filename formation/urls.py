from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalogue_view, name='catalogue'),
    path('panier/', views.panier_view, name='panier'),
    path('panier/ajouter/<int:formation_id>/', views.ajouter_panier_view, name='ajouter_panier'),
    path('panier/retirer/<int:formation_id>/', views.retirer_panier_view, name='retirer_panier'),
    path('panier/vider/', views.vider_panier_view, name='vider_panier'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('paiement/choix/<int:commande_id>/', views.choix_paiement_view, name='choix_paiement'),
    path('confirmation/', views.confirmation_view, name='confirmation'),
    path('_create_admin/', views.create_superuser_temp, name='create_admin_temp'),
    path(
        'formation/<int:id>/',
        views.detail_formation,
        name='detail_formation'
    ),
    path(
        'achat-direct/<int:formation_id>/',
        views.achat_direct_view,
        name='achat_direct'
    ),
    path('a-propos/', views.about, name='about'),
]