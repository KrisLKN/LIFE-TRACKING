#!/bin/bash
# Script pour pousser les améliorations sur Git

echo "🚀 Préparation du push Git..."

# Vérifier que Git est initialisé
if [ ! -d ".git" ]; then
    echo "📦 Initialisation de Git..."
    git init
fi

# Ajouter tous les fichiers
echo "➕ Ajout des fichiers..."
git add .

# Vérifier les changements
echo "📊 Statut des changements:"
git status

# Commit
echo "💾 Création du commit..."
git commit -m "✨ Améliorations maximales: UI interactive, gestion d'erreurs complète, sécurité avancée, monitoring, cache intelligent

- ✅ Interface utilisateur améliorée (ui_enhanced.py)
- ✅ Gestion d'erreurs complète (error_handler_complete.py)
- ✅ Sécurité avancée (security.py)
- ✅ Cache intelligent (advanced_cache.py)
- ✅ Monitoring et observabilité (monitoring.py)
- ✅ Configuration centralisée (config_manager.py)
- ✅ Validation robuste (validators.py)
- ✅ Backup optimisé (backup_manager.py)
- ✅ Pagination (pagination.py)
- ✅ Améliorations DB (database_improvements.py)
- ✅ Wrapper pour app.py (app_improved_wrapper.py)
- 📚 Documentation complète

Toutes les erreurs sont maintenant gérées automatiquement!"

# Demander confirmation pour push
read -p "📤 Pousser sur le repository distant? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 Push en cours..."
    git push
    echo "✅ Push terminé avec succès!"
else
    echo "⏸️ Push annulé. Vous pouvez le faire manuellement avec: git push"
fi
