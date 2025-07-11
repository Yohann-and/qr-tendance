# Dockerfile pour le déploiement sur Render
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements
COPY pyproject.toml uv.lock ./

# Installer uv et les dépendances
RUN pip install uv
RUN uv sync --frozen

# Copier le code de l'application
COPY . .

# Créer le répertoire .streamlit s'il n'existe pas
RUN mkdir -p .streamlit

# Configurer Streamlit pour la production
RUN echo "[server]\nheadless = true\naddress = \"0.0.0.0\"\nport = 8501\nenableCORS = false\nenableXsrfProtection = false\n" > .streamlit/config.toml

# Exposer le port
EXPOSE 8501

# Commande de démarrage
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]