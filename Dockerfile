# Dockerfile pour le déploiement sur Render
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt ./

# Installer les dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copier le reste de l'application
COPY . .

# Créer le dossier .streamlit et y mettre la config de production
RUN mkdir -p .streamlit
RUN echo "[server]\nheadless = true\naddress = \"0.0.0.0\"\nport = 8501\nenableCORS = false\nenableXsrfProtection = false\n" > .streamlit/config.toml

# Exposer le port Streamlit
EXPOSE 8501

# Commande pour lancer l'application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
