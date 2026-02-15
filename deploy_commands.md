# Commandes Git pour Déployer sur GitHub

## 📝 Commandes à exécuter dans PowerShell

Ouvrez PowerShell dans le dossier du projet et exécutez ces commandes une par une :

```powershell
# 1. Aller dans le dossier du projet
cd "C:\Users\LOKOUN Kris\Desktop\projects\Task planner"

# 2. Initialiser Git (si pas déjà fait)
git init

# 3. Vérifier les fichiers à ajouter
git status

# 4. Ajouter tous les fichiers
git add .

# 5. Faire le premier commit
git commit -m "Application planificateur avec design minimaliste et mode nuit"

# 6. Renommer la branche en main
git branch -M main

# 7. Ajouter le remote GitHub (REMPLACEZ par votre URL)
git remote add origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git

# 8. Pousser sur GitHub
git push -u origin main
```

## ⚠️ Important

- Remplacez `VOTRE_USERNAME` par votre nom d'utilisateur GitHub
- Remplacez `VOTRE_REPO` par le nom de votre repository GitHub
- Si vous avez déjà un remote, utilisez : `git remote set-url origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git`

## 🔄 Pour les mises à jour futures

```powershell
git add .
git commit -m "Description de vos modifications"
git push
```
