from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from django.http import HttpResponse
import stripe
from twilio.rest import Client
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .utils import envoyer_sms, envoyer_email_html

from .models import *
from .forms import produitForm
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST

from django.core.mail import send_mail

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

# ===================== Liste des produits =====================
def liste_produits(request):
    categorie_id = request.GET.get('categorie')
    produit_id = request.GET.get('produit')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort_by', 'nom')
    order = request.GET.get('order', 'asc')

    produits = Produit.objects.filter(disponible=True).order_by('nom')
    categories = Categorie.objects.all()

    # Filtrage par produit
    if produit_id:
        produits = produits.filter(id=produit_id)

    # Filtrage par catégorie
    if categorie_id:
        produits = produits.filter(categorie__id=categorie_id)

    # Filtrage par prix
    if min_price:
        produits = produits.filter(prix__gte=min_price)
    if max_price:
        produits = produits.filter(prix__lte=max_price)

    # Tri
    if order == 'desc':
        sort_by = '-' + sort_by
    produits = produits.order_by(sort_by)

    context = {
        'produits': produits,
        'categories': categories,
        'categorie_id': int(categorie_id) if categorie_id else None,
        'produit_id': int(produit_id) if produit_id else None,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by.lstrip('-'),
        'order': order,
    }
    return render(request, 'produit/liste_produits.html', context)


def detail_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    images = produit.images.all()

    # Produits similaires (même catégorie, exclure le produit actuel)
    produits_similaires = Produit.objects.filter(
        categorie=produit.categorie
    ).exclude(id=produit.id)[:8]  # Limite à 8

    return render(request, "produit/detail_produit.html", {
        "produit": produit,
        "images": images,
        "produits_similaires": produits_similaires,
    })




def panier(request):
    panier_session = request.session.get('panier', {})
    produits = []
    total_general = 0

    for produit_id, quantite in panier_session.items():
        produit = get_object_or_404(Produit, pk=produit_id)
        sous_total = produit.prix * quantite
        total_general += sous_total
        produits.append({
            'produit': produit,
            'quantite': quantite,
            'sous_total': sous_total,
            'prix': produit.prix
        })

    context = {
        'produits': produits,
        'total_general': total_general,
        'afficher_formulaire': not request.user.is_authenticated
    }
    return render(request, 'produit/panier.html', context)




from django.contrib import messages


def ajouter_panier(request, produit_id):
    produit = get_object_or_404(Produit, pk=produit_id)

    # Vérifie la disponibilité du produit
    if produit.quantite <= 0:
        messages.error(request, f"Le produit '{produit.nom}' n'est plus disponible.")
        return redirect('liste_produits')

    # Récupération du panier depuis la session
    panier_session = request.session.get('panier', {})

    # Si le produit est déjà dans le panier, on incrémente la quantité
    if str(produit.id) in panier_session:
        panier_session[str(produit.id)] += 1
    else:
        panier_session[str(produit.id)] = 1

    # On sauvegarde le panier dans la session
    request.session['panier'] = panier_session
    messages.success(request, f"Produit '{produit.nom}' ajouté au panier.")
    return redirect('panier')




def annuler_du_panier(request, produit_id):
    panier = request.session.get('panier', {})
    if str(produit_id) in panier:
        del panier[str(produit_id)]
        request.session['panier'] = panier
        messages.success(request, "Produit retiré du panier.")
    return redirect('panier')

def vider_panier(request):
    request.session['panier'] = {}
    messages.success(request, "Panier vidé.")
    return redirect('panier')



def valider_panier(request):
    if request.method == "POST":
        # Récupération des infos client
        nom = request.POST.get("nom")
        prenom = request.POST.get("prenom")
        email = request.POST.get("email")
        telephone = request.POST.get("telephone")
        adresse = request.POST.get("adresse")
        paiement = request.POST.get("paiement")

        # Vérifier qu'un mode de paiement est sélectionné
        if not paiement:
            messages.error(request, "Veuillez choisir un mode de paiement.")
            return redirect("panier")

        # Récupération du panier dans la session
        panier = request.session.get("panier", {})
        if not panier:
            messages.error(request, "Votre panier est vide ❌")
            return redirect("panier")

        # Calcul du total
        total = 0
        for pid, quantite in panier.items():
            produit = get_object_or_404(Produit, pk=pid)
            total += produit.prix * quantite

        # Création de la commande
        commande = Commande.objects.create(
            client=request.user if request.user.is_authenticated else None,
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            adresse=adresse,
            mode_paiement=paiement,
            total=total
        )

        # Traitement selon le mode de paiement
        if paiement == "livraison":
            # Paiement à la livraison → aucune info supplémentaire
            messages.info(request, "Vous avez choisi le paiement à la livraison.")
        elif paiement == "carte":
            # Paiement par carte
            carte_numero = request.POST.get("carte_numero")
            carte_expiration = request.POST.get("carte_expiration")
            carte_cvv = request.POST.get("carte_cvv")
            if not carte_numero or not carte_expiration or not carte_cvv:
                messages.error(request, "Veuillez remplir toutes les informations de votre carte.")
                return redirect("panier")
            messages.info(request, "Paiement par carte enregistré.")  # Ici tu pourrais intégrer un paiement réel
        elif paiement == "mobile":
            # Mobile Money
            money_type = request.POST.get("moneyType")
            numero = None
            if money_type == "orange":
                numero = request.POST.get("orange_numero")
            elif money_type == "moov":
                numero = request.POST.get("moov_numero")
            elif money_type == "wave":
                numero = request.POST.get("wave_numero")
            if not money_type or not numero:
                messages.error(request, "Veuillez remplir le numéro pour Mobile Money.")
                return redirect("panier")
            messages.info(request, f"Paiement Mobile Money ({money_type}) enregistré.")
        else:
            messages.error(request, "Mode de paiement non valide.")
            return redirect("panier")

        # Création des lignes de commande
        for pid, quantite in panier.items():
            produit = get_object_or_404(Produit, pk=pid)
            LigneCommande.objects.create(
                commande=commande,
                produit=produit,
                quantite=quantite,
                prix_unitaire=produit.prix
            )

        # Vider le panier
        request.session["panier"] = {}

        messages.success(request, "✅ Votre commande a été validée avec succès !")
        return redirect("liste_produits")

    return redirect("panier")



# ===================== Gestion des produits =====================
@login_required
def ajouter_produit(request):
    if request.method == 'POST':
        form = produitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('liste_produits')
    else:
        form = produitForm()
    return render(request, 'produit/ajouter_produit.html', {'form': form})


@login_required
def modifier_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    if request.method == 'POST':
        form = produitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            form.save()
            return redirect('liste_produits')
    else:
        form = produitForm(instance=produit)
    return render(request, 'produit/modifier_produit.html', {'form': form})


@login_required
def supprimer_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    if request.method == 'POST':
        produit.delete()
        return redirect('liste_produits')
    return render(request, 'produit/supprimer_produit.html', {'produit': produit})


# ===================== Inscription =====================
def inscription(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('liste_produits')
    else:
        form = UserCreationForm()
    return render(request, 'utilisateurs/inscription.html', {'form': form})


def deconnexion(request):
    logout(request)
    return redirect('liste_produits')


# ===================== Paiement Stripe =====================
def payment_complete(request):
    commande_id = request.GET.get('commande_id')
    commande = Commande.objects.get(id=commande_id)
    try:
        payment_intent = stripe.PaymentIntent.retrieve(request.GET.get('payment_intent'))
        if payment_intent['status'] == 'succeeded':
            commande.paye = True
            commande.save()
            return render(request, 'payment/payment_success.html', {'commande': commande})
        else:
            return HttpResponse('Échec du paiement', status=400)
    except stripe.error.StripeError as e:
        return HttpResponse(f'Erreur Stripe: {e}', status=400)


def payment_view(request):
    panier_id = request.GET.get('panier_id')
    panier = Panier.objects.get(id=panier_id)
    intent = stripe.PaymentIntent.create(
        amount=int(panier.total * 100),
        currency='eur',
        metadata={'panier_id': panier.id},
    )
    return render(request, 'payment/payment_form.html', {
        'client_secret': intent.client_secret,
        'panier': panier
    })

@login_required
def mes_commandes(request):
    commandes = Commande.objects.filter(client=request.user).order_by("-date")
    return render(request, "mes_commandes.html", {"commandes": commandes})




from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Commande
  # Assure-toi que ta fonction SMS est bien importée

@staff_member_required
@require_POST
def changer_statut_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    nouveau_statut = request.POST.get("statut")

    if nouveau_statut in dict(Commande.STATUT_CHOICES):
        commande.statut = nouveau_statut
        commande.save()

        # ---- Notification Email HTML ----
        subject = f"⚡ Mise à jour de votre commande #{commande.id}"
        from_email = "no-reply@tonsite.com"
        to_email = [commande.email]

        # Message texte brut pour fallback
        message_txt = f"""
Bonjour {commande.nom},

Votre commande #{commande.id} a changé de statut.
➡️ Nouveau statut : {dict(Commande.STATUT_CHOICES)[nouveau_statut]}
Montant total : {commande.total} FCFA

Merci pour votre confiance 🙏
"""

        # Message HTML stylisé façon e-commerce
        html_content = render_to_string("emails/confirmation_commande.html", {
            "commande": commande,
            "nouveau_statut": dict(Commande.STATUT_CHOICES)[nouveau_statut],
        })

        email = EmailMultiAlternatives(subject, message_txt, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)

        # ---- Notification SMS ----
        if commande.telephone:
            sms_message = f"Votre commande #{commande.id} est maintenant : {dict(Commande.STATUT_CHOICES)[nouveau_statut]}"
            envoyer_sms(commande.telephone, sms_message)

    return redirect("gestion_commandes")






def envoyer_sms(numero, message):
    """
    Envoie un SMS via Twilio.
    """
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    twilio_number = settings.TWILIO_PHONE_NUMBER

    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        from_=twilio_number,
        to=numero
    )





def send_order_status_email(commande, nouveau_statut):
    """
    Envoie un email HTML stylisé au client quand le statut de la commande change.
    - commande : instance de Commande
    - nouveau_statut : clé du statut (ex: 'en_cours', 'livree', ...)
    """

    # Préparer le contexte pour le template
    statut_label = dict(commande._meta.get_field('statut').choices).get(nouveau_statut, nouveau_statut)
    contexte = {
        "commande": commande,
        "statut_label": statut_label,
        "site_name": "MonSite",
        "support_email": "support@monsite.com",
        # tu peux ajouter des URLs réelles si tu veux (ex: lien suivi)
        "commande_url": f"https://www.monsite.com/mes-commandes/{commande.id}/",
    }

    # Rendu HTML et texte brut
    html_content = render_to_string("emails/order_status.html", contexte)
    text_content = strip_tags(html_content)  # fallback simple ; tu peux aussi fournir un template texte séparé

    subject = f"[MonSite] Mise à jour de votre commande #{commande.id} — {statut_label}"
    from_email = "no-reply@monsite.com"
    to = [commande.email]

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    # Envoi, fail_silently=False en dev pour voir erreurs
    msg.send(fail_silently=False)





def preview_email(request):
    produits = [
        {'produit': {'nom': 'Produit A', 'image': {'url': '/static/images/produit_a.jpg'}}, 'quantite': 2, 'prix_unitaire': 1000, 'sous_total': 2000},
        {'produit': {'nom': 'Produit B', 'image': {'url': '/static/images/produit_b.jpg'}}, 'quantite': 1, 'prix_unitaire': 1500, 'sous_total': 1500},
    ]
    context = {
        'client_nom': 'Jean Dupont',
        'commande_id': 123,
        'date_commande': timezone.now(),
        'produits': produits,
        'total': 3500,
        'mode_paiement': 'carte',
        'site_url': 'http://127.0.0.1:8000',
        'annee': timezone.now().year,
    }
    return render(request, 'emails/confirmation_commande.html', context)


def valider_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    
    # Mise à jour du statut de la commande
    commande.statut = 'CONFIRMEE'
    commande.save()

    # Envoi SMS si le client a un numéro
    if commande.telephone:
        sms_message = f"Votre commande #{commande.id} est confirmée !"
        envoyer_sms(commande.telephone, sms_message)

    # Envoi email HTML de confirmation
    envoyer_email_html(
        sujet=f"Commande #{commande.id} confirmée",
        template="emails/confirmation_commande.html",
        context={"commande": commande},
        destinataire=commande.email
    )

    # Message Django
    messages.success(request, f"Commande #{commande.id} validée, SMS et email envoyés !")

    # Redirection
    return redirect('mes_commandes')

def produits_par_categorie(request, categorie_id):
    categorie = get_object_or_404(Categorie, id=categorie_id)
    produits = Produit.objects.filter(category=categorie)
    return render(request, 'produit/produits_par_categorie.html', {'categorie': categorie, 'produits': produits})


def services(request):
    """Affiche la page des services de l'entreprise."""
    return render(request, 'produit/services.html')