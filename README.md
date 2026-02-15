# 📅 Planificateur d'Événements - Gestionnaire Complet de Vie (Second Cerveau)

Une application Streamlit complète pour gérer toute votre vie : tracker vos événements, gérer vos études, organiser vos connaissances (second cerveau), avec notifications par Email et Telegram.

## 🚀 Fonctionnalités Principales

### 📅 Gestion d'Événements
- ✅ **Ajout d'événements** : Enregistrez tous vos événements (sport, travail, repas, sommeil, etc.)
- 📊 **Tableau de bord** : Visualisez et filtrez tous vos événements
- 📈 **Statistiques** : Graphiques et analyses de vos activités
- 🗓️ **Calendrier** : Vue calendrier de vos événements
- 🏋️ **Suivi Sport** : Tracking spécialisé pour vos séances de sport avec objectif de 5 séances/jour
- 📤 **Export** : Export CSV, Excel et PDF de vos données

### 🏫 Gestion Scolaire
- 📚 **Examens** : Planifiez vos examens avec rappels automatiques
- 📖 **Cours** : Gérez votre emploi du temps
- 📝 **Devoirs** : Suivez vos devoirs avec priorités
- 🍱 **Rappel Tupperware** : Rappel automatique la veille des jours d'école

### 🧠 Second Cerveau
- 📝 **Notes** : Créez et organisez vos notes avec tags et catégories
- 🔗 **Liens** : Sauvegardez vos ressources et liens importants
- 💡 **Connaissances** : Organisez vos éléments de connaissance avec relations

### 🔔 Notifications Intelligentes
- 📧 **Email** : Recevez des rappels par email
- 💬 **Telegram** : Recevez des notifications Telegram
- ⏰ **Rappels automatiques** : Pour examens, Tupperware, événements

## 📦 Installation

1. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

2. **Lancer l'application** :
```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

## 🎨 Design Minimaliste

L'application utilise un design minimaliste noir et blanc avec :
- **Icônes Font Awesome** : Toutes les icônes sont remplacées par des icônes Font Awesome professionnelles
- **Mode Nuit** : Toggle manuel dans la sidebar + détection automatique du mode système
- **Interface épurée** : Design épuré et moderne pour une expérience utilisateur optimale
- **Thème adaptatif** : S'adapte automatiquement à vos préférences système

### Utilisation du Mode Nuit

- Cliquez sur le bouton "Mode Nuit" / "Mode Jour" dans la sidebar pour basculer manuellement
- Le mode suit automatiquement les préférences de votre système (si aucune préférence manuelle n'est définie)

## 🌐 Déploiement sur Streamlit Cloud

### Prérequis

1. **Compte GitHub** : Votre code doit être sur GitHub
2. **Compte Streamlit Cloud** : Créez un compte gratuit sur [Streamlit Cloud](https://streamlit.io/cloud)

### Étapes de Déploiement

1. **Pousser le code sur GitHub** :
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
   git push -u origin main
   ```

2. **Connecter à Streamlit Cloud** :
   - Allez sur [share.streamlit.io](https://share.streamlit.io)
   - Cliquez sur "New app"
   - Connectez votre compte GitHub
   - Sélectionnez votre repository

3. **Configurer l'application** :
   - **Main file path** : `app.py`
   - **Python version** : 3.8+ (détecté automatiquement)
   - **Branch** : `main` (ou votre branche principale)

4. **Variables d'environnement** (optionnel, pour les notifications) :
   - Dans les paramètres de l'app sur Streamlit Cloud
   - Ajoutez les variables d'environnement nécessaires :
     - `EMAIL_ENABLED`, `EMAIL_SMTP_SERVER`, `EMAIL_SMTP_PORT`, `EMAIL_SENDER`, `EMAIL_PASSWORD`
     - `TELEGRAM_ENABLED`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

5. **Déployer** :
   - Cliquez sur "Deploy"
   - Votre application sera accessible via une URL `https://votre-app.streamlit.app`
   - **L'application reste en ligne 24/7, même si votre ordinateur est éteint !**

### Mise à Jour

À chaque push sur GitHub, Streamlit Cloud redéploie automatiquement votre application.

## 📁 Structure du Projet

```
Task planner/
├── .streamlit/
│   └── config.toml         # Configuration Streamlit (thème, serveur)
├── assets/
│   └── style.css           # CSS personnalisé (design minimaliste)
├── app.py                  # Application principale Streamlit
├── theme.py                # Gestion du thème (mode nuit, icônes)
├── database.py             # Gestion SQLite + backup JSON
├── models.py               # Modèles de données
├── config.py               # Configuration et constantes
├── utils.py                # Fonctions utilitaires (export, stats)
├── notifications.py        # Service de notifications Email/Telegram
├── check_reminders.py      # Script pour vérifier les rappels
├── requirements.txt        # Dépendances Python
├── README.md              # Documentation
├── tracker.db             # Base de données SQLite (créé automatiquement)
└── events_data.json       # Backup JSON (créé automatiquement)
```

## 💾 Stockage des Données

Les données sont stockées dans une base de données SQLite (`tracker.db`) avec backup automatique vers JSON (`events_data.json`). Toutes les modifications sont sauvegardées automatiquement.

## 🎯 Utilisation

### Configuration des Notifications

#### Email (Gmail)
1. Activez l'authentification à 2 facteurs sur votre compte Gmail
2. Générez un mot de passe d'application
3. Configurez les variables d'environnement :
```bash
export EMAIL_ENABLED=true
export EMAIL_SMTP_SERVER=smtp.gmail.com
export EMAIL_SMTP_PORT=587
export EMAIL_SENDER=votre_email@gmail.com
export EMAIL_PASSWORD=votre_mot_de_passe_app
```

#### Telegram
1. Créez un bot avec @BotFather sur Telegram
2. Obtenez votre chat_id en envoyant un message à votre bot puis visitez :
   `https://api.telegram.org/bot<VOTRE_TOKEN>/getUpdates`
3. Configurez les variables d'environnement :
```bash
export TELEGRAM_ENABLED=true
export TELEGRAM_BOT_TOKEN=votre_token
export TELEGRAM_CHAT_ID=votre_chat_id
```

### Utilisation de l'Application

1. **Dashboard** : Vue d'ensemble avec métriques clés
2. **Ajouter Événement** : Enregistrez vos activités avec détails
3. **École** : Gérez examens, cours, devoirs et rappels Tupperware
4. **Second Cerveau** : Organisez vos notes, liens et connaissances
5. **Statistiques** : Analysez vos données avec graphiques
6. **Configuration** : Configurez Email et Telegram

### Rappels Automatiques

Pour activer les rappels automatiques, exécutez périodiquement :
```bash
python check_reminders.py
```

Ou configurez un cron job :
```bash
# Vérifier toutes les heures
0 * * * * cd /chemin/vers/projet && python check_reminders.py
```

## 🏋️ Objectif Sport

L'application track spécialement vos séances de sport avec un objectif de **5 séances par jour**. Les statistiques montrent votre progression vers cet objectif.

## 🧠 Second Cerveau

Organisez toutes vos connaissances :
- **Notes** : Idées, réflexions, apprentissages avec tags
- **Liens** : Ressources importantes classées par catégorie
- **Connaissances** : Concepts, méthodes, références avec relations

## 🏫 Gestion Scolaire

- **Examens** : Planifiez avec rappels automatiques (configurables)
- **Cours** : Emploi du temps avec rappel Tupperware
- **Devoirs** : Suivi avec priorités et statuts

## 📝 Notes Techniques

- Les données sont sauvegardées automatiquement dans SQLite
- Backup JSON automatique après chaque modification
- Tous les graphiques sont interactifs grâce à Plotly
- Migration automatique depuis JSON existant vers SQLite

## 🔧 Personnalisation

Vous pouvez facilement personnaliser :
- Les types d'événements dans `config.py`
- L'objectif de séances de sport par jour
- Les catégories du second cerveau
- Le design et les couleurs dans `assets/style.css`
- Le thème par défaut dans `.streamlit/config.toml`
- Les icônes dans `theme.py` et `config.py`

### Personnalisation du Design

- **Couleurs** : Modifiez les variables CSS dans `assets/style.css`
- **Icônes** : Ajoutez de nouvelles icônes dans le mapping `ICON_MAPPING` de `config.py`
- **Thème** : Ajustez les couleurs du thème dans `.streamlit/config.toml`

---

**Bon tracking ! 💪**
