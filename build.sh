#!/usr/bin/env bash
# Script de build pour Render

# Sortir en cas d'erreur
set -o errexit

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Collecter les fichiers statiques
python manage.py collectstatic --noinput --clear

# Appliquer les migrations de base de données
python manage.py migrate