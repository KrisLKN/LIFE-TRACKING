# Script PowerShell pour pousser les améliorations sur Git

Write-Host "🚀 Préparation du push Git..." -ForegroundColor Cyan

# Vérifier que Git est initialisé
if (-not (Test-Path ".git")) {
    Write-Host "📦 Initialisation de Git..." -ForegroundColor Yellow
    git init
}

# Ajouter tous les fichiers
Write-Host "➕ Ajout des fichiers..." -ForegroundColor Green
git add .

# Vérifier les changements
Write-Host "`n📊 Statut des changements:" -ForegroundColor Cyan
git status

# Commit
Write-Host "`n💾 Création du commit..." -ForegroundColor Green
$commitMessage = @"
✨ Améliorations maximales: UI interactive, gestion d'erreurs complète, sécurité avancée, monitoring, cache intelligent

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

Toutes les erreurs sont maintenant gérées automatiquement!
"@

git commit -m $commitMessage

# Demander confirmation pour push
$response = Read-Host "`n📤 Pousser sur le repository distant? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host "📤 Push en cours..." -ForegroundColor Green
    git push
    Write-Host "✅ Push terminé avec succès!" -ForegroundColor Green
} else {
    Write-Host "⏸️ Push annulé. Vous pouvez le faire manuellement avec: git push" -ForegroundColor Yellow
}
