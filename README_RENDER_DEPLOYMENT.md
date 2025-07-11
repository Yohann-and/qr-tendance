# 🚀 Guide de Déploiement sur Render.com

## Dashboard Statistiques QR Pointage - Benj Média Production

### 📋 Pré-requis

1. **Compte Render.com** : Créez un compte sur [render.com](https://render.com)
2. **Repository Git** : Votre code doit être sur GitHub, GitLab ou Bitbucket
3. **Base de données PostgreSQL** : Base de données accessible depuis internet

### 🔧 Configuration du Service Web

#### 1. Créer un nouveau Web Service
- Connectez votre repository Git
- Choisissez "Web Service"
- Runtime : **Python 3**

#### 2. Configuration Build & Deploy
```bash
# Build Command
pip install uv && uv sync --frozen

# Start Command
./start.sh
```

#### 3. Variables d'Environnement Requises

**📊 Base de Données (OBLIGATOIRE)**
```
DATABASE_URL=postgresql://user:password@host:port/database
PGHOST=your-db-host
PGPORT=5432
PGDATABASE=your-database-name
PGUSER=your-username
PGPASSWORD=your-password
```

**📱 SMS Twilio (OPTIONNEL)**
```
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number
```

#### 4. Configuration Avancée
```
# Plan : Starter (gratuit) ou Professional
# Region : Oregon (US West) recommandée
# Auto-Deploy : Oui (pour les mises à jour automatiques)
```

### 🗄️ Configuration Base de Données

#### Option 1: Base PostgreSQL Existante
Utilisez votre base de données existante en configurant les variables d'environnement.

#### Option 2: Nouvelle Base Render PostgreSQL
1. Créez un service PostgreSQL sur Render
2. Récupérez l'URL de connexion
3. Configurez la variable DATABASE_URL

### 📁 Structure de la Table Requise

```sql
CREATE TABLE pointages (
    id SERIAL PRIMARY KEY,
    matricule VARCHAR(50) NOT NULL,
    date_pointage DATE NOT NULL,
    heure_pointage TIME,
    statut VARCHAR(20) NOT NULL CHECK (statut IN ('Présent', 'Absent', 'Retard')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour améliorer les performances
CREATE INDEX idx_pointages_matricule ON pointages(matricule);
CREATE INDEX idx_pointages_date ON pointages(date_pointage);
CREATE INDEX idx_pointages_statut ON pointages(statut);
```

### 🔐 Configuration Authentification

**Identifiants par défaut :**
- Utilisateur : `administrator`
- Mot de passe : `RichyMLG007`

⚠️ **Changez ces identifiants** après le premier déploiement via l'interface d'administration.

### 🔍 Vérification du Déploiement

1. **Test de Connexion** : Vérifiez l'accès à votre URL Render
2. **Test Base de Données** : Connectez-vous et vérifiez les données
3. **Test Fonctionnalités** :
   - Authentification
   - Dashboard principal
   - Chatbot IA
   - Système d'alertes
   - Prédictions
   - Génération de rapports

### 🚨 Dépannage

#### Erreur de Connexion Base de Données
```bash
# Vérifiez les variables d'environnement
echo $DATABASE_URL
echo $PGHOST

# Testez la connexion depuis le terminal Render
psql $DATABASE_URL -c "SELECT version();"
```

#### Erreur de Build
```bash
# Vérifiez les logs de build
# Assurez-vous que pyproject.toml et uv.lock sont présents
```

#### Port d'Écoute
```bash
# Render assigne automatiquement le port via $PORT
# L'application s'adapte automatiquement
```

### 📊 Monitoring

- **Logs** : Accessible via le dashboard Render
- **Métriques** : CPU, mémoire, requêtes
- **Alertes** : Configuration d'alertes de monitoring

### 🔄 Mises à Jour

1. **Automatiques** : Push sur la branche configurée
2. **Manuelles** : Via le dashboard Render
3. **Rollback** : Possibilité de revenir à une version précédente

### 📞 Support

En cas de problème :
1. Consultez les logs Render
2. Vérifiez les variables d'environnement
3. Testez la connexion base de données
4. Consultez la documentation Render.com

### 🎯 URL d'Accès Final

Après déploiement, votre application sera accessible à :
```
https://dashboard-qr-pointage.onrender.com
```

---

**Benj Média Production** - Dashboard QR Pointage v2.0