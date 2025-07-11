#!/bin/bash

# Script de démarrage pour Render.com
echo "🚀 Démarrage de l'application Dashboard QR Pointage..."

# Définir le port par défaut si non spécifié
export PORT=${PORT:-8501}

echo "📡 Démarrage sur le port $PORT"

# Lancer l'application Streamlit
uv run streamlit run app.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false