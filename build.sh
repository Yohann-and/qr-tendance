#!/bin/bash

# Script de build pour Render.com
echo "🚀 Début du build pour Render..."

# Installation des dépendances Python avec uv
echo "📦 Installation des dépendances..."
pip install uv
uv sync --frozen

# Création du répertoire .streamlit si nécessaire
mkdir -p .streamlit

echo "✅ Build terminé avec succès!"