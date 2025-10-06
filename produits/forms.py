from django import forms
from .models import Produit

class produitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['nom', 'description', 'prix', 'quantite', 'image', 'disponible', 'categorie']
