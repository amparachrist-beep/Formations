#!/usr/bin/env bash
# Script de build pour Render avec Python 3.11

set -o errexit
set -o pipefail

echo "=== Mise à jour de pip et setuptools ==="
pip install --upgrade pip setuptools wheel

echo "=== Installation des dépendances système pour Pillow ==="
# Pré-requis système pour Pillow (si disponibles)
apt-get update && apt-get install -y libjpeg-dev zlib1g-dev 2>/dev/null || true

echo "=== Installation des dépendances Python ==="
pip install -r requirements.txt --no-cache-dir

echo "=== Collecte des fichiers statiques ==="
python manage.py collectstatic --noinput --clear

echo "=== Application des migrations ==="
python manage.py migrate --noinput

echo "=== Build terminé avec succès ==="