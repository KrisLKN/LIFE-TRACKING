"""
Wrapper pour améliorer app.py avec le nouveau système de gestion d'erreurs
Remplace toutes les fonctions safe_db_operation par le système complet
"""
from error_handler_complete import (
    catch_all_errors, safe_execute, error_boundary_ui,
    get_error_handler, CompleteErrorHandler
)
from ui_enhanced import (
    quick_action_button, smart_input, enhanced_data_table,
    smart_form, quick_stats_cards, notification_banner,
    error_boundary, loading_spinner
)
from errors import ErrorHandler
import streamlit as st
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# FONCTIONS AMÉLIORÉES POUR REMPLACER LES ANCIENNES
# ============================================================================

@catch_all_errors(return_default=[], show_error=True)
def safe_db_operation_improved(operation, default_value=None, context: str = "db_operation"):
    """
    Version améliorée de safe_db_operation avec gestion complète des erreurs
    
    Args:
        operation: Fonction à exécuter
        default_value: Valeur par défaut en cas d'erreur
        context: Contexte pour le logging
    
    Returns:
        Résultat de l'opération ou default_value
    """
    return safe_execute(
        operation,
        default_return=default_value if default_value is not None else [],
        context=context
    )


def safe_get_all_events(db, filters=None, default_value=None):
    """Récupère tous les événements de manière sécurisée"""
    return safe_execute(
        lambda: db.get_all_events(filters=filters),
        default_return=default_value or [],
        context="get_all_events"
    )


def safe_add_event(db, **kwargs):
    """Ajoute un événement de manière sécurisée"""
    return safe_execute(
        lambda: db.add_event(**kwargs),
        default_return=None,
        context="add_event"
    )


def safe_delete_event(db, event_id):
    """Supprime un événement de manière sécurisée"""
    return safe_execute(
        lambda: db.delete_event(event_id),
        default_return=False,
        context="delete_event"
    )


def safe_get_exams(db, upcoming_only=False, default_value=None):
    """Récupère les examens de manière sécurisée"""
    return safe_execute(
        lambda: db.get_all_exams(upcoming_only=upcoming_only),
        default_return=default_value or [],
        context="get_exams"
    )


def safe_add_exam(db, **kwargs):
    """Ajoute un examen de manière sécurisée"""
    return safe_execute(
        lambda: db.add_exam(**kwargs),
        default_return=None,
        context="add_exam"
    )


def safe_get_assignments(db, status=None, default_value=None):
    """Récupère les devoirs de manière sécurisée"""
    return safe_execute(
        lambda: db.get_all_assignments(status=status),
        default_return=default_value or [],
        context="get_assignments"
    )


def safe_add_assignment(db, **kwargs):
    """Ajoute un devoir de manière sécurisée"""
    return safe_execute(
        lambda: db.add_assignment(**kwargs),
        default_return=None,
        context="add_assignment"
    )


def safe_get_courses(db, default_value=None):
    """Récupère les cours de manière sécurisée"""
    return safe_execute(
        lambda: db.get_all_courses(),
        default_return=default_value or [],
        context="get_courses"
    )


def safe_add_course(db, **kwargs):
    """Ajoute un cours de manière sécurisée"""
    return safe_execute(
        lambda: db.add_course(**kwargs),
        default_return=None,
        context="add_course"
    )


def safe_get_notes(db, category=None, tag=None, default_value=None):
    """Récupère les notes de manière sécurisée"""
    return safe_execute(
        lambda: db.get_all_notes(category=category, tag=tag),
        default_return=default_value or [],
        context="get_notes"
    )


def safe_add_note(db, **kwargs):
    """Ajoute une note de manière sécurisée"""
    return safe_execute(
        lambda: db.add_note(**kwargs),
        default_return=None,
        context="add_note"
    )


# ============================================================================
# FONCTIONS UTILITAIRES AMÉLIORÉES
# ============================================================================

@error_boundary_ui
def display_error_stats():
    """Affiche les statistiques d'erreurs dans la sidebar"""
    error_handler = get_error_handler()
    stats = error_handler.get_error_stats()
    
    with st.sidebar.expander("📊 Statistiques d'erreurs", expanded=False):
        st.metric("Total d'erreurs", stats['total_errors'])
        st.metric("Erreurs récentes", stats['recent_errors'])
        
        if stats['error_types']:
            st.write("**Types d'erreurs:**")
            for error_type, count in stats['error_types'].items():
                st.write(f"- {error_type}: {count}")


def show_error_history(limit: int = 5):
    """Affiche l'historique des erreurs"""
    error_handler = get_error_handler()
    history = error_handler.get_error_history(limit=limit)
    
    if history:
        with st.expander("📜 Historique des erreurs", expanded=False):
            for error_entry in history:
                st.write(f"**{error_entry['timestamp']}**")
                st.write(f"Contexte: {error_entry['context']}")
                st.write(f"Erreur: {error_entry['error'].get('type', 'Unknown')}")
                st.write(f"Message: {error_entry['error'].get('message', 'N/A')}")
                st.divider()


# ============================================================================
# DÉCORATEURS POUR PROTÉGER TOUTES LES FONCTIONS
# ============================================================================

def protect_all_errors(func):
    """
    Décorateur pour protéger n'importe quelle fonction contre toutes les erreurs
    
    Usage:
        @protect_all_errors
        def my_function():
            ...
    """
    return error_boundary_ui(catch_all_errors(return_default=None)(func))


# ============================================================================
# CONTEXTE MANAGER POUR GESTION D'ERREURS
# ============================================================================

class ErrorContext:
    """
    Contexte manager pour gérer les erreurs dans un bloc de code
    
    Usage:
        with ErrorContext("Chargement des données"):
            data = load_data()
    """
    
    def __init__(self, context_name: str, show_error: bool = True):
        self.context_name = context_name
        self.show_error = show_error
        self.error_handler = get_error_handler()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            error_info = self.error_handler.handle(
                exc_val,
                context=self.context_name,
                show_to_user=self.show_error
            )
            
            if self.show_error:
                user_message = self.error_handler.get_user_message(exc_val)
                st.error(f"❌ Erreur dans {self.context_name}: {user_message}")
            
            # Ne pas propager l'erreur
            return True
        
        return False
