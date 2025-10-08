#!/usr/bin/env bash
set -o errexit

# Installer les dépendances Python
pip install -r requirements.txt

# Collecter les fichiers statiques
python manage.py collectstatic --no-input

# Appliquer les migrations à la base de données
python manage.py migrate
