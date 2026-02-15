# Guide de Déploiement sur Streamlit Cloud

## 📋 Prérequis

1. Un compte GitHub (gratuit)
2. Un compte Streamlit Cloud (gratuit) : [share.streamlit.io](https://share.streamlit.io)

## 🚀 Étapes de Déploiement

### Étape 1 : Préparer le Repository GitHub

1. **Créer un nouveau repository sur GitHub** :
   - Allez sur [github.com](https://github.com)
   - Cliquez sur "New repository"
   - Nommez-le (ex: `task-planner` ou `planificateur-evenements`)
   - Choisissez "Public" (gratuit) ou "Private"
   - **Ne cochez PAS** "Initialize with README" (on a déjà un README)

2. **Initialiser Git dans votre projet** (si pas déjà fait) :
   ```bash
   cd "C:\Users\LOKOUN Kris\Desktop\projects\Task planner"
   git init
   ```

3. **Ajouter tous les fichiers** :
   ```bash
   git add .
   ```

4. **Faire le premier commit** :
   ```bash
   git commit -m "Initial commit - Application planificateur avec design minimaliste"
   ```

5. **Renommer la branche en main** :
   ```bash
   git branch -M main
   ```

6. **Connecter à GitHub** :
   ```bash
   git remote add origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
   ```
   (Remplacez VOTRE_USERNAME et VOTRE_REPO par vos valeurs)

7. **Pousser sur GitHub** :
   ```bash
   git push -u origin main
   ```

### Étape 2 : Déployer sur Streamlit Cloud

1. **Aller sur Streamlit Cloud** :
   - Visitez [share.streamlit.io](https://share.streamlit.io)
   - Connectez-vous avec votre compte GitHub

2. **Créer une nouvelle application** :
   - Cliquez sur "New app"
   - Si c'est votre première fois, autorisez l'accès à GitHub

3. **Configurer l'application** :
   - **Repository** : Sélectionnez votre repository (ex: `VOTRE_USERNAME/task-planner`)
   - **Branch** : `main` (ou `master` selon votre repo)
   - **Main file path** : `app.py`
   - **App URL** : Choisissez un nom unique (ex: `mon-planificateur`)

4. **Cliquer sur "Deploy"**

5. **Attendre le déploiement** :
   - Streamlit Cloud va installer les dépendances et lancer l'application
   - Cela prend généralement 1-2 minutes
   - Vous verrez les logs en temps réel

6. **Votre application est en ligne !** :
   - URL : `https://mon-planificateur.streamlit.app`
   - L'application reste en ligne 24/7, même si votre ordinateur est éteint

### Étape 3 : Configuration Optionnelle (Notifications)

Si vous voulez utiliser les notifications Email/Telegram :

1. **Dans Streamlit Cloud**, allez dans les paramètres de votre app
2. **Cliquez sur "Secrets"** dans le menu
3. **Ajoutez les variables d'environnement** :

   Pour Email :
   ```
   EMAIL_ENABLED=true
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_SENDER=votre_email@gmail.com
   EMAIL_PASSWORD=votre_mot_de_passe_app
   ```

   Pour Telegram :
   ```
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=votre_token
   TELEGRAM_CHAT_ID=votre_chat_id
   ```

4. **Sauvegarder** - L'application redémarre automatiquement

## 🔄 Mise à Jour

À chaque fois que vous modifiez le code :

1. **Faire les modifications** dans votre code local
2. **Commit et push sur GitHub** :
   ```bash
   git add .
   git commit -m "Description des modifications"
   git push
   ```
3. **Streamlit Cloud redéploie automatiquement** votre application (1-2 minutes)

## ✅ Vérification

Après le déploiement, vérifiez que :
- ✅ L'application se charge correctement
- ✅ Les icônes Font Awesome s'affichent
- ✅ Le mode nuit fonctionne (toggle dans la sidebar)
- ✅ Toutes les pages sont accessibles
- ✅ Les graphiques s'affichent correctement

## 🐛 Problèmes Courants

### L'application ne se charge pas
- Vérifiez les logs dans Streamlit Cloud
- Vérifiez que `app.py` est bien à la racine
- Vérifiez que `requirements.txt` est présent

### Les icônes ne s'affichent pas
- Vérifiez votre connexion internet (Font Awesome est chargé depuis CDN)
- Vérifiez la console du navigateur pour les erreurs

### Erreur de module non trouvé
- Vérifiez que toutes les dépendances sont dans `requirements.txt`
- Vérifiez les logs de déploiement dans Streamlit Cloud

## 📞 Support

- Documentation Streamlit Cloud : [docs.streamlit.io/streamlit-community-cloud](https://docs.streamlit.io/streamlit-community-cloud)
- Forum Streamlit : [discuss.streamlit.io](https://discuss.streamlit.io)
