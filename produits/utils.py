# produits/utils.py
from twilio.rest import Client
from django.conf import settings

from twilio.rest import Client
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def format_numero_afrique_ouest_auto(numero):
    numero = str(numero).replace(" ", "").replace("-", "")
    
    if numero.startswith("+"):
        return numero
    elif numero.startswith("00"):
        return "+" + numero[2:]
    elif numero.startswith("0"):
        prefix = "+223"  # Par défaut Mali
        return prefix + numero[1:]
    else:
        prefix = "+223"
        return prefix + numero

def envoyer_sms(numero, message):
    numero_formate = format_numero_afrique_ouest_auto(numero)
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=numero_formate
    )

# produits/utils.py

# --- Fonction pour envoyer un SMS ---
def envoyer_sms(numero, message):
    account_sid = "TON_SID"
    auth_token = "TON_TOKEN"
    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        from_="+1234567890",  # numéro Twilio
        to=numero
    )

# --- Fonction pour envoyer un email HTML ---
def envoyer_email_html(sujet, template, context, destinataire):
    html_message = render_to_string(template, context)
    plain_message = strip_tags(html_message)

    send_mail(
        sujet,
        plain_message,
        "no-reply@tonsite.com",
        [destinataire],
        html_message=html_message,
        fail_silently=False
    )
