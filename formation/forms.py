from django import forms
from .models import Client
import re


class ClientForm(forms.ModelForm):

    class Meta:
        model = Client
        fields = ['nom_complet', 'whatsapp', 'email']

        widgets = {
            'nom_complet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Jean Dupont',
                'required': True
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 06 123 45 67 ou +242061234567',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: jean@email.com',
                'required': True
            }),
        }

        labels = {
            'nom_complet': 'Nom complet *',
            'whatsapp': 'Numéro WhatsApp *',
            'email': 'Adresse email *',
        }

    # ==================== VALIDATIONS ====================

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp')

        # Supprimer espaces
        whatsapp = whatsapp.replace(" ", "")

        # Regex simple pour Congo (+242 ou 06/05)
        pattern = r'^(\+242)?0?[56]\d{7}$'

        if not re.match(pattern, whatsapp):
            raise forms.ValidationError(
                "Numéro invalide. Exemple : 06 123 45 67 ou +242061234567"
            )

        # Normaliser au format international (important pour WhatsApp)
        if whatsapp.startswith("0"):
            whatsapp = "242" + whatsapp[1:]
        elif whatsapp.startswith("+242"):
            whatsapp = whatsapp[1:]

        return whatsapp

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()

        # Empêche les doublons côté UX (même si get_or_create existe)
        if Client.objects.filter(email=email).exists():
            pass  # On laisse passer car tu utilises get_or_create

        return email

    def clean_nom_complet(self):
        nom = self.cleaned_data.get('nom_complet').strip()

        if len(nom) < 3:
            raise forms.ValidationError("Nom trop court.")

        return nom