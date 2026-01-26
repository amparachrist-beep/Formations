from django.contrib import admin
from django.utils.html import format_html
from .models import Formation, Client, Commande


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'prix', 'active', 'date_creation']
    list_filter = ['active', 'date_creation']
    search_fields = ['titre', 'description']
    list_editable = ['active']
    readonly_fields = ['date_creation', 'date_modification']

    fieldsets = (
        ('Informations principales', {
            'fields': ('titre', 'description', 'prix', 'image', 'active')
        }),
        ('Accès à la formation', {
            'fields': ('lien_youtube', 'lien_drive')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'email', 'whatsapp', 'date_inscription']
    search_fields = ['nom_complet', 'email', 'whatsapp']
    readonly_fields = ['date_inscription']
    list_filter = ['date_inscription']


from django.contrib import admin
from django.utils.html import format_html
from .models import Commande


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'client',
        'montant_total',
        'statut_badge',
        'date_commande',
    )

    list_filter = (
        'statut',
        'date_commande',
        'date_paiement',
    )

    search_fields = (
        'client__nom_complet',
        'client__email',
        'moneroo_transaction_id',
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
            # ✅ correction ici
            'fields': ('formations', 'montant_total')
        }),
        ('Statut et paiement', {
            'fields': (
                'statut',
                'moneroo_transaction_id',
                'moneroo_payment_url',
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

    # ✅ Obligatoire pour ManyToManyField
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
            '<span style="background-color:{}; color:white; padding:3px 10px; border-radius:4px;">{}</span>',
            color,
            obj.get_statut_display()
        )

    statut_badge.short_description = 'Statut'

    actions = ['marquer_acces_envoye']

    def marquer_acces_envoye(self, request, queryset):
        updated = queryset.filter(statut='paye').update(statut='acces_envoye')
        self.message_user(
            request,
            f'{updated} commande(s) marquée(s) comme "Accès envoyé".'
        )

    marquer_acces_envoye.short_description = "Marquer les accès comme envoyés"
