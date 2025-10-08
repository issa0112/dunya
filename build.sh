#!/usr/bin/env bash
set -o errexit

# Installe les dépendances
pip install -r requirements.txt

# Rassemble les fichiers statiques
python manage.py collectstatic --no-input

# Applique les migrations
python manage.py migrate

