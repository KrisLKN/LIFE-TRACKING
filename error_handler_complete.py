"""
Gestionnaire d'erreurs complet - Gère TOUTES les erreurs possibles
- Capture toutes les exceptions
- Messages utilisateur-friendly
- Logging détaillé
- Récupération automatique
"""
import traceback
import sys
from typing import Any, Callable, Optional, Dict
from functools import wraps
import logging
from datetime import datetime

from errors import (
    ErrorHandler, AppException, DatabaseError, ValidationError,
    DatabaseConnectionError, DatabaseIntegrityError, DatabaseNotFoundError,
    BusinessLogicError, SystemError, ConfigurationError
)

logger = logging.getLogger(__name__)


class CompleteErrorHandler:
    """
    Gestionnaire d'erreurs complet qui capture TOUTES les exceptions
    """
    
    def __init__(self):
        self.error_count = 0
        self.error_history = []
        self.max_history = 100
    
    def handle(self, exception: Exception, context: str = None, show_to_user: bool = True) -> Dict[str, Any]:
        """
        Gère n'importe quelle exception de manière complète
        
        Args:
            exception: Exception à gérer
            context: Contexte de l'erreur
            show_to_user: Afficher à l'utilisateur
        
        Returns:
            Dictionnaire avec les informations d'erreur
        """
        self.error_count += 1
        
        # Logger l'erreur
        error_info = self._log_error(exception, context)
        
        # Ajouter à l'historique
        self.error_history.append({
            'timestamp': datetime.now().isoformat(),
            'error': error_info,
            'context': context
        })
        
        # Limiter l'historique
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # Retourner les informations
        return error_info
    
    def _log_error(self, exception: Exception, context: str = None) -> Dict[str, Any]:
        """Log l'erreur avec tous les détails"""
        error_type = type(exception).__name__
        error_message = str(exception)
        traceback_str = traceback.format_exc()
        
        # Déterminer le niveau de log
        if isinstance(exception, (ValidationError, DatabaseNotFoundError)):
            log_level = logging.WARNING
        elif isinstance(exception, (DatabaseError, BusinessLogicError)):
            log_level = logging.ERROR
        else:
            log_level = logging.CRITICAL
        
        # Logger
        logger.log(
            log_level,
            f"Erreur dans {context or 'unknown'}: {error_type}: {error_message}",
            exc_info=True
        )
        
        # Créer le dictionnaire d'erreur
        error_info = {
            'type': error_type,
            'message': error_message,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback_str,
            'is_critical': log_level >= logging.ERROR
        }
        
        # Ajouter des informations spécifiques selon le type
        if isinstance(exception, AppException):
            error_info.update(exception.to_dict())
        
        return error_info
    
    def get_user_message(self, exception: Exception) -> str:
        """
        Retourne un message convivial pour l'utilisateur
        
        Args:
            exception: Exception
        
        Returns:
            Message utilisateur-friendly
        """
        # Messages spécifiques par type d'erreur
        if isinstance(exception, ValidationError):
            return f"❌ Données invalides: {exception.message}"
        
        elif isinstance(exception, DatabaseConnectionError):
            return "❌ Impossible de se connecter à la base de données. Veuillez réessayer."
        
        elif isinstance(exception, DatabaseIntegrityError):
            return "❌ Erreur de données. Vérifiez que toutes les informations sont correctes."
        
        elif isinstance(exception, DatabaseNotFoundError):
            return f"❌ {exception.message}"
        
        elif isinstance(exception, DatabaseError):
            return "❌ Erreur de base de données. Veuillez réessayer plus tard."
        
        elif isinstance(exception, BusinessLogicError):
            return f"❌ {exception.message}"
        
        elif isinstance(exception, SystemError):
            return "❌ Erreur système. Veuillez contacter le support si le problème persiste."
        
        elif isinstance(exception, ConfigurationError):
            return f"❌ Erreur de configuration: {exception.message}"
        
        elif isinstance(exception, ValueError):
            return f"❌ Valeur invalide: {str(exception)}"
        
        elif isinstance(exception, KeyError):
            return f"❌ Clé manquante: {str(exception)}"
        
        elif isinstance(exception, AttributeError):
            return f"❌ Attribut manquant: {str(exception)}"
        
        elif isinstance(exception, TypeError):
            return f"❌ Type incorrect: {str(exception)}"
        
        elif isinstance(exception, FileNotFoundError):
            return f"❌ Fichier non trouvé: {str(exception)}"
        
        elif isinstance(exception, PermissionError):
            return "❌ Permission refusée. Vérifiez les droits d'accès."
        
        elif isinstance(exception, TimeoutError):
            return "❌ Délai d'attente dépassé. Veuillez réessayer."
        
        elif isinstance(exception, MemoryError):
            return "❌ Mémoire insuffisante. Fermez d'autres applications."
        
        elif isinstance(exception, KeyboardInterrupt):
            return "⚠️ Opération annulée par l'utilisateur"
        
        else:
            # Message générique pour les exceptions inconnues
            return f"❌ Une erreur inattendue s'est produite: {type(exception).__name__}"
    
    def get_error_history(self, limit: int = 10) -> list:
        """Retourne l'historique des erreurs"""
        return self.error_history[-limit:]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'erreurs"""
        error_types = {}
        for error in self.error_history:
            error_type = error['error'].get('type', 'Unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': self.error_count,
            'recent_errors': len(self.error_history),
            'error_types': error_types
        }


# Instance globale
_complete_error_handler = CompleteErrorHandler()


def catch_all_errors(
    show_error: bool = True,
    return_default: Any = None,
    log_error: bool = True,
    context: str = None
):
    """
    Décorateur qui capture TOUTES les exceptions
    
    Usage:
        @catch_all_errors(return_default=[])
        def get_data():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Gérer l'erreur
                error_info = _complete_error_handler.handle(
                    e,
                    context=context or func.__name__,
                    show_to_user=show_error
                )
                
                # Logger si demandé
                if log_error:
                    logger.error(f"Erreur dans {func.__name__}: {e}", exc_info=True)
                
                # Retourner la valeur par défaut
                return return_default
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    error_message: str = None,
    context: str = None,
    **kwargs
) -> Any:
    """
    Exécute une fonction de manière sécurisée avec gestion complète des erreurs
    
    Args:
        func: Fonction à exécuter
        *args: Arguments positionnels
        default_return: Valeur à retourner en cas d'erreur
        error_message: Message d'erreur personnalisé
        context: Contexte de l'exécution
        **kwargs: Arguments nommés
    
    Returns:
        Résultat de la fonction ou default_return
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_info = _complete_error_handler.handle(e, context=context or func.__name__)
        
        user_message = error_message or _complete_error_handler.get_user_message(e)
        logger.error(f"Erreur dans safe_execute: {e}", exc_info=True)
        
        return default_return


def error_boundary_ui(func: Callable, error_title: str = "Erreur"):
    """
    Wrapper UI qui affiche les erreurs dans Streamlit
    
    Args:
        func: Fonction à exécuter
        error_title: Titre de l'erreur
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            import streamlit as st
            
            error_info = _complete_error_handler.handle(e, context=func.__name__)
            user_message = _complete_error_handler.get_user_message(e)
            
            # Afficher l'erreur
            st.error(f"**{error_title}**")
            st.error(user_message)
            
            # Détails techniques (si debug activé)
            if st.session_state.get('debug_mode', False):
                with st.expander("🔍 Détails techniques"):
                    st.json(error_info)
                    st.code(error_info.get('traceback', ''), language='python')
            
            # Suggestions de résolution
            suggestions = _get_suggestions(e)
            if suggestions:
                st.info("💡 **Suggestions:**\n" + "\n".join(f"- {s}" for s in suggestions))
            
            return None
    
    return wrapper


def _get_suggestions(exception: Exception) -> list:
    """Retourne des suggestions de résolution selon le type d'erreur"""
    suggestions = []
    
    if isinstance(exception, DatabaseConnectionError):
        suggestions.extend([
            "Vérifiez que la base de données est accessible",
            "Vérifiez les permissions d'accès au fichier",
            "Redémarrez l'application"
        ])
    
    elif isinstance(exception, ValidationError):
        suggestions.extend([
            "Vérifiez le format des données saisies",
            "Assurez-vous que tous les champs obligatoires sont remplis",
            "Consultez les exemples de format dans l'aide"
        ])
    
    elif isinstance(exception, DatabaseNotFoundError):
        suggestions.extend([
            "Vérifiez que l'élément existe",
            "Actualisez la liste",
            "Vérifiez l'ID ou le nom"
        ])
    
    elif isinstance(exception, FileNotFoundError):
        suggestions.extend([
            "Vérifiez que le fichier existe",
            "Vérifiez le chemin du fichier",
            "Vérifiez les permissions d'accès"
        ])
    
    elif isinstance(exception, PermissionError):
        suggestions.extend([
            "Vérifiez les permissions d'accès",
            "Exécutez en tant qu'administrateur si nécessaire",
            "Vérifiez les droits d'écriture"
        ])
    
    elif isinstance(exception, MemoryError):
        suggestions.extend([
            "Fermez d'autres applications",
            "Réduisez la taille des données",
            "Redémarrez l'application"
        ])
    
    return suggestions


def get_error_handler() -> CompleteErrorHandler:
    """Retourne l'instance globale du gestionnaire d'erreurs"""
    return _complete_error_handler
