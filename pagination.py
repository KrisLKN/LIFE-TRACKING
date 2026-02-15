"""
Système de pagination pour les grandes listes
Améliore les performances en chargeant uniquement les données nécessaires
"""
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import math


@dataclass
class PaginatedResult:
    """Résultat paginé avec métadonnées"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    total_pages: int
    
    @property
    def has_next(self) -> bool:
        """Vérifie s'il y a une page suivante"""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Vérifie s'il y a une page précédente"""
        return self.page > 1
    
    @property
    def start_index(self) -> int:
        """Index de début (1-based)"""
        return (self.page - 1) * self.per_page + 1 if self.total > 0 else 0
    
    @property
    def end_index(self) -> int:
        """Index de fin (1-based)"""
        return min(self.page * self.per_page, self.total)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation"""
        return {
            'items': self.items,
            'pagination': {
                'total': self.total,
                'page': self.page,
                'per_page': self.per_page,
                'total_pages': self.total_pages,
                'has_next': self.has_next,
                'has_previous': self.has_previous,
                'start_index': self.start_index,
                'end_index': self.end_index
            }
        }


class Paginator:
    """
    Gestionnaire de pagination générique
    
    Supporte deux modes:
    1. Pagination en mémoire (toutes les données chargées)
    2. Pagination avec callback (chargement à la demande)
    """
    
    @staticmethod
    def paginate(
        items: List[Dict[str, Any]],
        page: int = 1,
        per_page: int = 50
    ) -> PaginatedResult:
        """
        Pagine une liste d'éléments en mémoire
        
        Args:
            items: Liste complète des éléments
            page: Numéro de page (commence à 1)
            per_page: Nombre d'éléments par page
        
        Returns:
            PaginatedResult avec les éléments de la page demandée
        """
        total = len(items)
        total_pages = math.ceil(total / per_page) if total > 0 else 1
        
        # Valider et ajuster le numéro de page
        page = max(1, min(page, total_pages))
        
        # Calculer les indices
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Extraire les éléments de la page
        page_items = items[start_idx:end_idx]
        
        return PaginatedResult(
            items=page_items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    
    @staticmethod
    def paginate_with_callback(
        callback: Callable[[int, int], List[Dict[str, Any]]],
        count_callback: Callable[[], int],
        page: int = 1,
        per_page: int = 50
    ) -> PaginatedResult:
        """
        Pagine avec des callbacks pour le chargement à la demande
        
        Args:
            callback: Fonction qui retourne les items (offset, limit)
            count_callback: Fonction qui retourne le nombre total
            page: Numéro de page (commence à 1)
            per_page: Nombre d'éléments par page
        
        Returns:
            PaginatedResult avec les éléments de la page demandée
        """
        total = count_callback()
        total_pages = math.ceil(total / per_page) if total > 0 else 1
        
        # Valider et ajuster le numéro de page
        page = max(1, min(page, total_pages))
        
        # Calculer l'offset
        offset = (page - 1) * per_page
        
        # Récupérer les éléments
        page_items = callback(offset, per_page)
        
        return PaginatedResult(
            items=page_items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )


class DatabasePaginator:
    """
    Paginateur spécialisé pour les requêtes de base de données
    Optimise les requêtes avec LIMIT et OFFSET
    """
    
    def __init__(self, db_instance):
        """
        Initialise le paginateur de base de données
        
        Args:
            db_instance: Instance de la classe Database
        """
        self.db = db_instance
    
    def paginate_events(
        self,
        page: int = 1,
        per_page: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> PaginatedResult:
        """
        Pagine les événements avec filtres optionnels
        
        Args:
            page: Numéro de page
            per_page: Éléments par page
            filters: Dictionnaire de filtres (type, date_from, date_to)
        
        Returns:
            PaginatedResult avec les événements paginés
        """
        # Récupérer tous les événements (pour le total)
        # Note: Pour de très grandes bases, on pourrait optimiser avec COUNT(*)
        all_events = self.db.get_all_events(filters=filters)
        return Paginator.paginate(all_events, page=page, per_page=per_page)
    
    def paginate_exams(
        self,
        page: int = 1,
        per_page: int = 50,
        upcoming_only: bool = False
    ) -> PaginatedResult:
        """
        Pagine les examens
        
        Args:
            page: Numéro de page
            per_page: Éléments par page
            upcoming_only: Si True, uniquement les examens à venir
        
        Returns:
            PaginatedResult avec les examens paginés
        """
        all_exams = self.db.get_all_exams(upcoming_only=upcoming_only)
        return Paginator.paginate(all_exams, page=page, per_page=per_page)
    
    def paginate_assignments(
        self,
        page: int = 1,
        per_page: int = 50,
        status: Optional[str] = None
    ) -> PaginatedResult:
        """
        Pagine les devoirs
        
        Args:
            page: Numéro de page
            per_page: Éléments par page
            status: Filtrer par statut (optionnel)
        
        Returns:
            PaginatedResult avec les devoirs paginés
        """
        all_assignments = self.db.get_all_assignments(status=status)
        return Paginator.paginate(all_assignments, page=page, per_page=per_page)
    
    def paginate_notes(
        self,
        page: int = 1,
        per_page: int = 50,
        category: Optional[str] = None,
        tag: Optional[str] = None
    ) -> PaginatedResult:
        """
        Pagine les notes
        
        Args:
            page: Numéro de page
            per_page: Éléments par page
            category: Filtrer par catégorie (optionnel)
            tag: Filtrer par tag (optionnel)
        
        Returns:
            PaginatedResult avec les notes paginées
        """
        all_notes = self.db.get_all_notes(category=category, tag=tag)
        return Paginator.paginate(all_notes, page=page, per_page=per_page)


# ============================================================================
# FONCTIONS UTILITAIRES POUR STREAMLIT
# ============================================================================

def render_pagination_controls(result: PaginatedResult, key_prefix: str = "page"):
    """
    Affiche les contrôles de pagination dans Streamlit
    
    Args:
        result: PaginatedResult à afficher
        key_prefix: Préfixe pour les clés de session state
    """
    import streamlit as st
    
    if result.total_pages <= 1:
        return  # Pas besoin de pagination
    
    # Informations de pagination
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    
    with col1:
        if result.has_previous:
            if st.button("← Précédent", key=f"{key_prefix}_prev"):
                st.session_state[f"{key_prefix}_current"] = result.page - 1
                st.rerun()
    
    with col2:
        st.write(f"**Page {result.page} / {result.total_pages}**")
    
    with col3:
        st.write(f"*{result.start_index}-{result.end_index} sur {result.total}*")
    
    with col4:
        if result.has_next:
            if st.button("Suivant →", key=f"{key_prefix}_next"):
                st.session_state[f"{key_prefix}_current"] = result.page + 1
                st.rerun()
    
    # Sélecteur de page direct
    if result.total_pages > 5:
        selected_page = st.selectbox(
            "Aller à la page:",
            range(1, result.total_pages + 1),
            index=result.page - 1,
            key=f"{key_prefix}_selector"
        )
        if selected_page != result.page:
            st.session_state[f"{key_prefix}_current"] = selected_page
            st.rerun()
