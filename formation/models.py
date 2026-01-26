from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Formation(models.Model):
    titre = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix (FCFA)"
    )
    image = models.ImageField(
        upload_to='formation/',
        null=True,
        blank=True,
        verbose_name="Image"
    )
    lien_youtube = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="Lien YouTube (privé)"
    )
    lien_drive = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="Lien Google Drive"
    )
    active = models.BooleanField(default=True, verbose_name="Active")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['-date_creation']

    def __str__(self):
        return self.titre


class Client(models.Model):
    nom_complet = models.CharField(max_length=200, verbose_name="Nom complet")
    whatsapp = models.CharField(max_length=20, verbose_name="Numéro WhatsApp")
    email = models.EmailField(verbose_name="Email")
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['-date_inscription']

    def __str__(self):
        return f"{self.nom_complet} ({self.email})"


class Commande(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('paye', 'Payé'),
        ('annule', 'Annulé'),
        ('acces_envoye', 'Accès envoyé'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    formations = models.ManyToManyField(Formation)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente'
    )

    # Informations Moneroo
    moneroo_transaction_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )
    moneroo_payment_url = models.URLField(
        max_length=500,
        blank=True,
        null=True
    )

    date_commande = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(null=True, blank=True)
    date_acces_envoye = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_commande']

    def __str__(self):
        return f"Commande #{self.id} - {self.client.nom_complet}"

    def marquer_comme_paye(self):
        self.statut = 'paye'
        self.date_paiement = timezone.now()
        self.save()

    def marquer_acces_envoye(self):
        self.statut = 'acces_envoye'
        self.date_acces_envoye = timezone.now()
        self.save()