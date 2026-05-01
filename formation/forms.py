from django import forms
from .models import Client
import re
import phonenumbers
from django.core.exceptions import ValidationError


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
                'placeholder': 'Ex:+242061234567',
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

        # nettoyage basique
        whatsapp = whatsapp.replace(" ", "").replace("-", "")

        # ❌ obligatoire : doit commencer par +
        if not whatsapp.startswith("+"):
            raise ValidationError(
                "Veuillez entrer votre numéro avec l'indicatif international. "
                "Exemples : +242061234567, +33 612345678"
            )

        try:
            number = phonenumbers.parse(whatsapp, None)

            if not phonenumbers.is_valid_number(number):
                raise ValidationError(
                    "Numéro invalide. Vérifiez l'indicatif et le format."
                )

            return phonenumbers.format_number(
                number,
                phonenumbers.PhoneNumberFormat.E164
            )

        except phonenumbers.NumberParseException:
            raise ValidationError(
                "Format invalide. Exemple attendu : +242061234567"
            )

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