# 🚀 Guide Complet de Déploiement sur Streamlit Cloud

## ✅ Vérification Préalable

Avant de commencer, assurez-vous que tous ces fichiers sont présents :
- ✅ `app.py` (fichier principal)
- ✅ `requirements.txt` (dépendances)
- ✅ `.streamlit/config.toml` (configuration)
- ✅ `assets/style.css` (styles)
- ✅ `theme.py` (gestion du thème)
- ✅ Tous les autres fichiers Python nécessaires

## 📦 ÉTAPE 1 : Créer le Repository GitHub

### 1.1 Aller sur GitHub
1. Ouvrez votre navigateur
2. Allez sur [github.com](https://github.com)
3. Connectez-vous (ou créez un compte si nécessaire)

### 1.2 Créer un nouveau repository
1. Cliquez sur le **"+"** en haut à droite → **"New repository"**
2. **Repository name** : Choisissez un nom (ex: `task-planner` ou `planificateur`)
3. **Description** (optionnel) : "Planificateur d'événements avec design minimaliste"
4. Choisissez **Public** (gratuit) ou **Private**
5. **⚠️ IMPORTANT** : Ne cochez PAS "Add a README file" (on en a déjà un)
6. Cliquez sur **"Create repository"**

### 1.3 Copier l'URL du repository
Après la création, GitHub vous montre une page avec des instructions. **Copiez l'URL HTTPS** qui ressemble à :
```
https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
```

## 💻 ÉTAPE 2 : Préparer le Code Local

### 2.1 Ouvrir PowerShell
1. Appuyez sur `Windows + X`
2. Choisissez **"Windows PowerShell"** ou **"Terminal"**
3. Naviguez vers votre projet :
```powershell
cd "C:\Users\LOKOUN Kris\Desktop\projects\Task planner"
```

### 2.2 Initialiser Git (si pas déjà fait)
```powershell
git init
```

### 2.3 Vérifier les fichiers
```powershell
git status
```
Vous devriez voir tous vos fichiers listés.

### 2.4 Ajouter tous les fichiers
```powershell
git add .
```

### 2.5 Faire le premier commit
```powershell
git commit -m "Application planificateur avec design minimaliste et mode nuit"
```

### 2.6 Renommer la branche en main
```powershell
git branch -M main
```

### 2.7 Connecter à GitHub
**Remplacez `VOTRE_USERNAME` et `VOTRE_REPO` par vos valeurs réelles** :
```powershell
git remote add origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
```

### 2.8 Pousser sur GitHub
```powershell
git push -u origin main
```

**Si c'est la première fois**, GitHub vous demandera de vous connecter :
- Entrez votre nom d'utilisateur GitHub
- Pour le mot de passe, utilisez un **Personal Access Token** (pas votre mot de passe)
  - Pour créer un token : GitHub → Settings → Developer settings → Personal access tokens → Generate new token
  - Cochez "repo" dans les permissions
  - Copiez le token et utilisez-le comme mot de passe

## 🌐 ÉTAPE 3 : Déployer sur Streamlit Cloud

### 3.1 Aller sur Streamlit Cloud
1. Ouvrez [share.streamlit.io](https://share.streamlit.io) dans votre navigateur
2. Cliquez sur **"Sign in"** ou **"Get started"**
3. Choisissez **"Continue with GitHub"**
4. Autorisez l'accès à GitHub si demandé

### 3.2 Créer une nouvelle application
1. Cliquez sur **"New app"** (bouton en haut à droite)
2. Si c'est votre première fois, vous devrez peut-être autoriser Streamlit Cloud à accéder à vos repositories GitHub

### 3.3 Configurer l'application
Remplissez le formulaire :

- **Repository** : Sélectionnez votre repository dans la liste déroulante
  - Ex: `VOTRE_USERNAME/task-planner`

- **Branch** : `main` (ou `master` selon votre repository)

- **Main file path** : `app.py`
  - ⚠️ C'est le fichier principal de votre application

- **App URL** : Choisissez un nom unique pour l'URL
  - Ex: `mon-planificateur` ou `task-planner-kris`
  - L'URL finale sera : `https://mon-planificateur.streamlit.app`

### 3.4 Déployer
1. Cliquez sur **"Deploy"**
2. Attendez 1-2 minutes pendant que Streamlit Cloud :
   - Installe les dépendances depuis `requirements.txt`
   - Lance votre application
   - Vous pouvez voir les logs en temps réel

### 3.5 Vérifier le déploiement
Une fois terminé, vous verrez :
- ✅ Un message "Your app is live!"
- ✅ L'URL de votre application
- ✅ Un bouton "View app" pour ouvrir l'application

## 🎉 Votre Application est en Ligne !

Votre application est maintenant accessible 24/7 à l'adresse :
```
https://VOTRE-APP-NAME.streamlit.app
```

**L'application fonctionne même si votre ordinateur est éteint !** 🚀

## 🔄 Mettre à Jour l'Application

Chaque fois que vous modifiez le code :

1. **Faire les modifications** dans votre code local

2. **Dans PowerShell**, dans le dossier du projet :
```powershell
git add .
git commit -m "Description de vos modifications"
git push
```

3. **Streamlit Cloud redéploie automatiquement** (1-2 minutes)
   - Vous recevrez un email de confirmation
   - L'application se met à jour automatiquement

## ⚙️ Configuration Optionnelle : Notifications

Si vous voulez utiliser les notifications Email/Telegram :

1. Dans Streamlit Cloud, allez sur votre application
2. Cliquez sur **"⚙️ Settings"** (en haut à droite)
3. Cliquez sur **"Secrets"** dans le menu de gauche
4. Ajoutez vos variables d'environnement dans le format TOML :

```toml
EMAIL_ENABLED = "true"
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = "587"
EMAIL_SENDER = "votre_email@gmail.com"
EMAIL_PASSWORD = "votre_mot_de_passe_app"

TELEGRAM_ENABLED = "true"
TELEGRAM_BOT_TOKEN = "votre_token"
TELEGRAM_CHAT_ID = "votre_chat_id"
```

5. Cliquez sur **"Save"** - L'application redémarre automatiquement

## ✅ Checklist de Vérification

Après le déploiement, vérifiez que :

- [ ] L'application se charge sans erreur
- [ ] Les icônes Font Awesome s'affichent correctement
- [ ] Le mode nuit fonctionne (toggle dans la sidebar)
- [ ] Toutes les pages sont accessibles (Dashboard, Ajouter Événement, etc.)
- [ ] Les graphiques s'affichent correctement
- [ ] Le design minimaliste est appliqué

## 🐛 Résolution de Problèmes

### L'application ne se charge pas
- Vérifiez les **logs** dans Streamlit Cloud (onglet "Logs")
- Vérifiez que `app.py` est bien à la racine du repository
- Vérifiez que `requirements.txt` contient toutes les dépendances

### Erreur "Module not found"
- Vérifiez que toutes les dépendances sont dans `requirements.txt`
- Vérifiez les logs pour voir quel module manque

### Les icônes ne s'affichent pas
- Vérifiez votre connexion internet (Font Awesome est chargé depuis CDN)
- Ouvrez la console du navigateur (F12) pour voir les erreurs

### Erreur lors du push Git
- Vérifiez que vous êtes connecté à GitHub
- Utilisez un Personal Access Token au lieu du mot de passe
- Vérifiez que l'URL du remote est correcte : `git remote -v`

## 📞 Support

- **Documentation Streamlit Cloud** : [docs.streamlit.io/streamlit-community-cloud](https://docs.streamlit.io/streamlit-community-cloud)
- **Forum Streamlit** : [discuss.streamlit.io](https://discuss.streamlit.io)
- **GitHub Issues** : Créez une issue sur votre repository

---

**Bon déploiement ! 🚀**
