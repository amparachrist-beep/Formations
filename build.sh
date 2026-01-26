#!/usr/bin/env bash
set -o errexit

echo "=== Installation des dépendances ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Collecte des fichiers statiques ==="
python manage.py collectstatic --noinput --clear

echo "=== Application des migrations ==="
python manage.py migrate --noinput

echo "=== Build terminé ==="