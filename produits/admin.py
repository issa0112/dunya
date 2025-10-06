from django.contrib import admin
from .models import *

class ProduitImageInline(admin.TabularInline):
    model = ProduitImage
    extra = 3  # possibilité d’ajouter plusieurs images

class ProduitAdmin(admin.ModelAdmin):
    list_display = ("nom", "prix", "quantite", "disponible", "categorie")
    inlines = [ProduitImageInline]

# Enregistrer les modèles
admin.site.register(Categorie)                 # une seule fois
admin.site.register(Produit, ProduitAdmin)     # Produit avec son admin personnalisé
admin.site.register(LigneCommande)
admin.site.register(Commande)
admin.site.register(LignePanier)
admin.site.register(Panier)
