"""
Exemples de code pour implémenter certaines améliorations proposées
Ce fichier contient des exemples de patterns et d'implémentations à suivre
"""

# ============================================================================
# AMÉLIORATION #4 : Validation des entrées utilisateur avec Pydantic
# ============================================================================

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional
from datetime import datetime
import re

class EventCreate(BaseModel):
    """Modèle de validation pour la création d'événements"""
    type: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    datetime_str: str
    date_str: str
    time_str: str
    duration: int = Field(default=0, ge=0, le=1440)  # 0 à 1440 minutes (24h)
    notes: Optional[str] = Field(default="", max_length=5000)
    
    @validator('date_str')
    def validate_date(cls, v):
        """Valide le format de date"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Format de date invalide. Utilisez YYYY-MM-DD')
    
    @validator('time_str')
    def validate_time(cls, v):
        """Valide le format d'heure"""
        try:
            datetime.strptime(v, '%H:%M')
            return v
        except ValueError:
            raise ValueError('Format d\'heure invalide. Utilisez HH:MM')
    
    @validator('type')
    def validate_type(cls, v):
        """Valide le type d'événement"""
        allowed_types = ['Sport', 'Repas', 'Sommeil', 'Poids', 'Hydratation', 'Travail']
        if not any(allowed in v for allowed in allowed_types):
            raise ValueError(f'Type d\'événement invalide. Types autorisés: {", ".join(allowed_types)}')
        return v


class LinkCreate(BaseModel):
    """Modèle de validation pour les liens"""
    title: str = Field(..., min_length=1, max_length=200)
    url: HttpUrl  # Validation automatique d'URL
    description: Optional[str] = Field(default="", max_length=1000)
    tags: Optional[str] = Field(default="", max_length=500)
    category: Optional[str] = Field(default="", max_length=100)
    note_id: Optional[int] = Field(default=None, ge=1)


# ============================================================================
# AMÉLIORATION #8 : Backup JSON asynchrone avec cache
# ============================================================================

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Optional
import time

class AsyncBackupManager:
    """Gestionnaire de backup asynchrone avec cache"""
    
    def __init__(self, db_instance, backup_interval_minutes: int = 5):
        self.db = db_instance
        self.backup_interval = timedelta(minutes=backup_interval_minutes)
        self.last_backup: Optional[datetime] = None
        self.backup_lock = threading.Lock()
        self._backup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start_backup_service(self):
        """Démarre le service de backup en arrière-plan"""
        if self._backup_thread is None or not self._backup_thread.is_alive():
            self._stop_event.clear()
            self._backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
            self._backup_thread.start()
            logger.info("Service de backup démarré")
    
    def stop_backup_service(self):
        """Arrête le service de backup"""
        self._stop_event.set()
        if self._backup_thread:
            self._backup_thread.join(timeout=5)
        logger.info("Service de backup arrêté")
    
    def _backup_loop(self):
        """Boucle de backup périodique"""
        while not self._stop_event.is_set():
            try:
                if self._should_backup():
                    self._perform_backup()
                # Attendre l'intervalle ou jusqu'à l'arrêt
                self._stop_event.wait(self.backup_interval.total_seconds())
            except Exception as e:
                logger.error(f"Erreur dans la boucle de backup: {e}")
                time.sleep(60)  # Attendre 1 minute en cas d'erreur
    
    def _should_backup(self) -> bool:
        """Vérifie si un backup est nécessaire"""
        if self.last_backup is None:
            return True
        return datetime.now() - self.last_backup >= self.backup_interval
    
    def _perform_backup(self):
        """Effectue le backup"""
        with self.backup_lock:
            try:
                self.db.backup_to_json()
                self.last_backup = datetime.now()
                logger.info(f"Backup effectué à {self.last_backup}")
            except Exception as e:
                logger.error(f"Erreur lors du backup: {e}")
    
    def request_immediate_backup(self):
        """Demande un backup immédiat (pour opérations critiques)"""
        self._perform_backup()


# ============================================================================
# AMÉLIORATION #9 : Pagination pour les grandes listes
# ============================================================================

from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class PaginatedResult:
    """Résultat paginé"""
    items: List[Dict]
    total: int
    page: int
    per_page: int
    total_pages: int
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        return self.page > 1


class PaginatedQuery:
    """Helper pour les requêtes paginées"""
    
    @staticmethod
    def paginate_query(
        query_func,
        page: int = 1,
        per_page: int = 50,
        **query_kwargs
    ) -> PaginatedResult:
        """
        Pagine les résultats d'une requête
        
        Args:
            query_func: Fonction qui retourne tous les résultats
            page: Numéro de page (commence à 1)
            per_page: Nombre d'éléments par page
            **query_kwargs: Arguments à passer à query_func
        
        Returns:
            PaginatedResult avec les items de la page demandée
        """
        # Récupérer tous les résultats (pour le total)
        all_items = query_func(**query_kwargs)
        total = len(all_items)
        
        # Calculer la pagination
        total_pages = (total + per_page - 1) // per_page  # Arrondi supérieur
        page = max(1, min(page, total_pages))  # Clamper entre 1 et total_pages
        
        # Extraire les items de la page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_items = all_items[start_idx:end_idx]
        
        return PaginatedResult(
            items=page_items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )


# Exemple d'utilisation dans Streamlit:
"""
def display_paginated_events(db, page: int = 1, per_page: int = 50):
    result = PaginatedQuery.paginate_query(
        db.get_all_events,
        page=page,
        per_page=per_page
    )
    
    # Afficher les événements
    for event in result.items:
        st.write(event)
    
    # Contrôles de pagination
    col1, col2, col3 = st.columns(3)
    with col1:
        if result.has_previous:
            if st.button("← Précédent"):
                st.session_state.page = page - 1
                st.rerun()
    with col2:
        st.write(f"Page {result.page} / {result.total_pages}")
    with col3:
        if result.has_next:
            if st.button("Suivant →"):
                st.session_state.page = page + 1
                st.rerun()
"""


# ============================================================================
# AMÉLIORATION #11 : Indexation de la base de données
# ============================================================================

def create_database_indexes(db_connection):
    """Crée les index pour améliorer les performances"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)",
        "CREATE INDEX IF NOT EXISTS idx_events_datetime ON events(datetime)",
        "CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)",
        "CREATE INDEX IF NOT EXISTS idx_exams_date ON exams(exam_date)",
        "CREATE INDEX IF NOT EXISTS idx_assignments_due_date ON assignments(due_date)",
        "CREATE INDEX IF NOT EXISTS idx_assignments_status ON assignments(status)",
        "CREATE INDEX IF NOT EXISTS idx_courses_day ON courses(day_of_week)",
        "CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category)",
    ]
    
    cursor = db_connection.cursor()
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            logger.info(f"Index créé: {index_sql}")
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'index {index_sql}: {e}")
    
    db_connection.commit()


# ============================================================================
# AMÉLIORATION #12 : Gestion d'erreurs améliorée
# ============================================================================

from enum import Enum
from typing import Optional

class DatabaseError(Exception):
    """Exception de base pour les erreurs de base de données"""
    pass

class ConnectionError(DatabaseError):
    """Erreur de connexion à la base de données"""
    pass

class QueryError(DatabaseError):
    """Erreur lors de l'exécution d'une requête"""
    pass

class ValidationError(DatabaseError):
    """Erreur de validation des données"""
    pass


def safe_database_operation(operation, error_message: str = "Erreur de base de données"):
    """
    Wrapper pour exécuter des opérations DB de manière sécurisée
    
    Args:
        operation: Fonction à exécuter
        error_message: Message d'erreur personnalisé
    
    Returns:
        Résultat de l'opération ou None en cas d'erreur
    """
    try:
        return operation()
    except sqlite3.OperationalError as e:
        logger.error(f"{error_message} (OperationalError): {e}")
        raise ConnectionError(f"Erreur de connexion: {e}") from e
    except sqlite3.IntegrityError as e:
        logger.error(f"{error_message} (IntegrityError): {e}")
        raise ValidationError(f"Erreur d'intégrité: {e}") from e
    except sqlite3.Error as e:
        logger.error(f"{error_message} (SQLiteError): {e}")
        raise DatabaseError(f"Erreur de base de données: {e}") from e
    except Exception as e:
        logger.error(f"{error_message} (Exception inattendue): {e}")
        raise DatabaseError(f"Erreur inattendue: {e}") from e


# ============================================================================
# AMÉLIORATION #16 : Recherche globale améliorée
# ============================================================================

class GlobalSearch:
    """Service de recherche globale unifiée"""
    
    def __init__(self, db):
        self.db = db
    
    def search_all(self, query: str, limit: int = 50) -> Dict[str, List[Dict]]:
        """
        Recherche dans tous les types de contenu
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats par type
        
        Returns:
            Dictionnaire avec les résultats par type
        """
        results = {
            'events': [],
            'exams': [],
            'assignments': [],
            'courses': [],
            'notes': [],
            'links': [],
            'knowledge_items': []
        }
        
        if not query or len(query.strip()) < 2:
            return results
        
        search_term = f"%{query.strip()}%"
        
        try:
            # Recherche dans les événements
            events = self.db.get_all_events()
            results['events'] = [
                e for e in events
                if query.lower() in str(e.get('name', '')).lower()
                or query.lower() in str(e.get('notes', '')).lower()
            ][:limit]
            
            # Recherche dans les examens
            exams = self.db.get_all_exams()
            results['exams'] = [
                e for e in exams
                if query.lower() in str(e.get('name', '')).lower()
                or query.lower() in str(e.get('subject', '')).lower()
            ][:limit]
            
            # Recherche dans les notes
            results['notes'] = self.db.search_notes(query)[:limit]
            
            # Recherche dans les connaissances
            results['knowledge_items'] = self.db.search_knowledge(query)[:limit]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche globale: {e}")
        
        return results
    
    def get_search_stats(self, results: Dict[str, List[Dict]]) -> Dict[str, int]:
        """Retourne les statistiques de recherche"""
        return {key: len(value) for key, value in results.items()}


# ============================================================================
# AMÉLIORATION #19 : Notifications push dans le navigateur
# ============================================================================

def check_browser_notifications_support() -> bool:
    """Vérifie si le navigateur supporte les notifications"""
    # Cette vérification doit être faite côté client (JavaScript)
    # Voir l'exemple JavaScript ci-dessous
    return True


# Code JavaScript à injecter dans Streamlit (via st.components.v1.html)
BROWSER_NOTIFICATION_JS = """
<script>
// Demander la permission pour les notifications
async function requestNotificationPermission() {
    if ('Notification' in window) {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }
    return false;
}

// Envoyer une notification
function sendBrowserNotification(title, options = {}) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: options.body || '',
            icon: options.icon || '/favicon.ico',
            badge: options.badge || '/favicon.ico',
            tag: options.tag || 'default',
            requireInteraction: options.requireInteraction || false
        });
    }
}

// Vérifier les rappels et envoyer des notifications
function checkAndNotifyReminders() {
    // Cette fonction devrait être appelée périodiquement
    // et récupérer les rappels depuis l'API backend
    fetch('/api/reminders/pending')
        .then(response => response.json())
        .then(reminders => {
            reminders.forEach(reminder => {
                sendBrowserNotification(reminder.title, {
                    body: reminder.message,
                    tag: `reminder-${reminder.id}`
                });
            });
        });
}

// Initialiser au chargement de la page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', requestNotificationPermission);
} else {
    requestNotificationPermission();
}

// Vérifier les rappels toutes les minutes
setInterval(checkAndNotifyReminders, 60000);
</script>
"""


# ============================================================================
# AMÉLIORATION #25 : Validation des données avec Pydantic
# ============================================================================

from pydantic import BaseModel, validator
from typing import List

class ExamCreate(BaseModel):
    """Modèle de validation pour les examens"""
    name: str = Field(..., min_length=1, max_length=200)
    subject: Optional[str] = Field(default=None, max_length=100)
    exam_date: str
    exam_time: Optional[str] = None
    location: Optional[str] = Field(default=None, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=2000)
    reminder_days_before: int = Field(default=1, ge=0, le=30)
    
    @validator('exam_date')
    def validate_exam_date(cls, v):
        """Valide que la date d'examen est dans le futur"""
        try:
            exam_date = datetime.strptime(v, '%Y-%m-%d').date()
            today = datetime.now().date()
            if exam_date < today:
                raise ValueError('La date d\'examen ne peut pas être dans le passé')
            return v
        except ValueError as e:
            if 'invalid' in str(e).lower() or 'date'):
                raise ValueError('Format de date invalide. Utilisez YYYY-MM-DD')
            raise
    
    @validator('exam_time')
    def validate_exam_time(cls, v):
        """Valide le format d'heure si fourni"""
        if v is None:
            return v
        try:
            datetime.strptime(v, '%H:%M')
            return v
        except ValueError:
            raise ValueError('Format d\'heure invalide. Utilisez HH:MM')


# ============================================================================
# Exemple d'utilisation dans app.py
# ============================================================================

"""
# Dans app.py, remplacer les validations manuelles par:

from EXEMPLES_AMELIORATIONS import EventCreate, ExamCreate, ValidationError

try:
    event_data = EventCreate(
        type=event_type,
        name=event_name,
        datetime_str=datetime_str,
        date_str=date_str,
        time_str=time_str,
        duration=duration,
        notes=notes
    )
    # Utiliser event_data.dict() pour obtenir les valeurs validées
    db.add_event(**event_data.dict())
    st.success("Événement ajouté avec succès!")
except ValidationError as e:
    st.error(f"Erreur de validation: {e}")
except Exception as e:
    st.error(f"Erreur inattendue: {e}")
"""
