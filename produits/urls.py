from django.urls import path
from . import views
from .views import *

urlpatterns = [
    # Produits
    path('', views.liste_produits, name='liste_produits'),
    path('liste/', liste_produits, name='liste_produits'),
    path('ajouter/', ajouter_produit, name='ajouter_produit'),
    path('modifier/<int:produit_id>/', modifier_produit, name='modifier_produit'),
    path('supprimer/<int:produit_id>/', supprimer_produit, name='supprimer_produit'),

    # Catégories
    path('categorie/<int:categorie_id>/', produits_par_categorie, name='produits_par_categorie'),
    
    # Panier
    path('panier/', views.panier, name='panier'),
    # path("ajouter-panier/<int:produit_id>/", views.ajouter_panier, name="ajouter_panier"),
    path('annuler/<int:produit_id>/', views.annuler_du_panier, name='annuler_du_panier'),
    path('vider/', views.vider_panier, name='vider_panier'),
    path('valider/', views.valider_panier, name='valider_panier'),
    # path('mes_paniers/', views.mes_paniers, name='mes_paniers'),
    path("produit/<int:produit_id>/", views.detail_produit, name="detail_produit"),
    path("ajouter-panier/<int:produit_id>/", views.ajouter_panier, name="ajouter_panier"),
    path("mes-commandes/", views.mes_commandes, name="mes_commandes"),
    path("admin-commandes/", views.gestion_commandes, name="gestion_commandes"),
    path("changer-statut/<int:commande_id>/", views.changer_statut_commande, name="changer_statut_commande"),
    path('preview-email/', preview_email, name='preview_email'),
    path('services/', views.services, name='services'),

]
