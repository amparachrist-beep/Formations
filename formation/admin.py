from django.contrib import admin
from django.utils.html import format_html
from .models import Formation, Client, Commande
from .utils import envoyer_acces_formation_email
from .models import FormationDetail, FormationImage

# ==================== FORMATION ====================

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'prix_affiche', 'active', 'date_creation']
    list_filter = ['active', 'date_creation']
    search_fields = ['titre', 'description']
    list_editable = ['active']
    readonly_fields = ['date_creation', 'date_modification']

    fieldsets = (
        ('Informations principales', {
            'fields': ('titre', 'description', 'prix', 'prix_promo', 'image', 'active')
        }),
        ('Accès à la formation', {
            'fields': ('lien_youtube', 'lien_drive', 'drive_folder_id')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description="Prix (actuel)")
    def prix_affiche(self, obj):
        return obj.prix_actuel

# ==================== CLIENT ====================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'email', 'whatsapp', 'date_inscription']
    search_fields = ['nom_complet', 'email', 'whatsapp']
    readonly_fields = ['date_inscription']
    list_filter = ['date_inscription']


# ==================== COMMANDE ====================

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'client',
        'montant_total',
        'operateur_paiement',
        'statut_badge',
        'date_commande',
    )

    list_filter = (
        'statut',
        'operateur_paiement',
        'date_commande',
        'date_paiement',
    )

    search_fields = (
        'client__nom_complet',
        'client__email',
        'reference_paiement',
    )

    readonly_fields = (
        'date_commande',
        'date_paiement',
        'date_acces_envoye',
    )

    fieldsets = (
        ('Informations client', {
            'fields': ('client',)
        }),
        ('Formations', {
            'fields': ('formations', 'montant_total')
        }),
        ('Statut et paiement', {
            'fields': (
                'statut',
                'operateur_paiement',
                'reference_paiement',
            )
        }),
        ('Dates', {
            'fields': (
                'date_commande',
                'date_paiement',
                'date_acces_envoye',
            )
        }),
    )

    filter_horizontal = ('formations',)

    def statut_badge(self, obj):
        colors = {
            'en_attente': 'orange',
            'paye': 'green',
            'annule': 'red',
            'acces_envoye': 'blue',
        }
        color = colors.get(obj.statut, 'gray')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 10px; '
            'border-radius:4px; font-weight:600;">{}</span>',
            color,
            obj.get_statut_display()
        )

    statut_badge.short_description = 'Statut'

    actions = ['marquer_paye_et_envoyer_acces', 'marquer_acces_envoye']

    def marquer_paye_et_envoyer_acces(self, request, queryset):
        """Marque les commandes en attente comme payées et envoie les accès par email"""
        succes = 0
        echec_email = 0

        for commande in queryset.filter(statut='en_attente'):
            commande.marquer_comme_paye()
            email_ok = envoyer_acces_formation_email(commande)
            if email_ok:
                commande.marquer_acces_envoye()
                succes += 1
            else:
                echec_email += 1

        if succes:
            self.message_user(
                request,
                f'✅ {succes} commande(s) validée(s) et accès envoyés par email.'
            )
        if echec_email:
            self.message_user(
                request,
                f'⚠️ {echec_email} commande(s) marquées payées mais échec envoi email.',
                level='warning'
            )

    marquer_paye_et_envoyer_acces.short_description = "✅ Marquer comme payé et envoyer les accès"

    def marquer_acces_envoye(self, request, queryset):
        """Marque manuellement les accès comme envoyés (sans email)"""
        updated = queryset.filter(statut='paye').update(statut='acces_envoye')
        self.message_user(
            request,
            f'{updated} commande(s) marquée(s) comme "Accès envoyé".'
        )

    marquer_acces_envoye.short_description = "📧 Marquer les accès comme envoyés (sans email)"




@admin.register(FormationDetail)
class FormationDetailAdmin(admin.ModelAdmin):
    list_display = (
        'formation',
    )

    search_fields = (
        'formation__titre',
        'description_complete',
    )

    list_select_related = (
        'formation',
    )


@admin.register(FormationImage)
class FormationImageAdmin(admin.ModelAdmin):
    list_display = (
        'formation',
        'titre',
        'image',
    )

    search_fields = (
        'formation__titre',
        'titre',
    )

    list_filter = (
        'formation',
    )

    list_select_related = (
        'formation',
    )