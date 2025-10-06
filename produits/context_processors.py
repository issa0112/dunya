from produits.models import Produit

def panier_count(request):
    panier = request.session.get('panier', {})
    total_articles = sum(panier.values())
    return {'panier_count': total_articles}
