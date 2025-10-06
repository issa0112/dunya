from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render   # <-- tu avais oublié ça !

# -----------------------------
# Catégorie
# -----------------------------
class Categorie(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


# -----------------------------
# Produit
# -----------------------------
class Produit(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    quantite = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='produits/', null=True, blank=True)
    disponible = models.BooleanField(default=True)
    date_expiration = models.DateField(null=True, blank=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True)

    def statut_quantite(self):
        if self.quantite < 5:
            return 'red'
        elif self.quantite <= 10:
            return 'orange'
        return 'green'

    def __str__(self):
        return self.nom

    def clean(self):
        if self.prix <= 0:
            raise ValidationError('Le prix doit être supérieur à zéro.')
        if not self.nom.strip():
            raise ValidationError('Le nom ne peut pas être vide.')


# -----------------------------
# Images supplémentaires d’un produit
# -----------------------------
class ProduitImage(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="produits/")


# -----------------------------
# Panier
# -----------------------------
class Panier(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # <-- j’ai mis default=0
    actif = models.BooleanField(default=True)  # panier en cours, pas encore validé

    def __str__(self):
        return f"Panier n°{self.id} de {self.client.username}"

    def get_total(self):
        return sum(l.sous_total() for l in self.lignes.all())


# -----------------------------
# Ligne Panier
# -----------------------------
class LignePanier(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    def sous_total(self):
        return self.quantite * self.prix_unitaire


# -----------------------------
# Commande
# -----------------------------
class Commande(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)

    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mode_paiement = models.CharField(max_length=50, default="livraison")

    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente'),
            ('en_cours', 'En cours de livraison'),
            ('livree', 'Livrée'),
            ('annulee', 'Annulée'),
        ],
        default='en_attente'
    )


# -----------------------------
# Ligne Commande
# -----------------------------
class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="lignes")
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire


# -----------------------------
# Vue admin commandes
# -----------------------------
@staff_member_required
def gestion_commandes(request):
    commandes = Commande.objects.all().order_by("-date")
    return render(request, "gestion_commandes.html", {"commandes": commandes})
