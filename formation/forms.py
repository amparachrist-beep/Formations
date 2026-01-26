from django import forms
from .models import Client

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom_complet', 'whatsapp', 'email']
        widgets = {
            'nom_complet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Jean Dupont'
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: +242 06 XXX XX XX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: jean.dupont@email.com'
            }),
        }
        labels = {
            'nom_complet': 'Nom complet *',
            'whatsapp': 'Numéro WhatsApp *',
            'email': 'Adresse email *',
        }