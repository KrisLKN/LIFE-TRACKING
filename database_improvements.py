"""
Améliorations de la logique de base de données
Intègre validation, gestion d'erreurs améliorée, et optimisations
"""
import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from errors import (
    DatabaseError, DatabaseConnectionError, DatabaseIntegrityError,
    DatabaseNotFoundError, ErrorHandler, handle_errors
)
from validators import (
    EventCreate, SportSessionCreate, ExerciseCreate, CardioActivityCreate,
    MealCreate, SleepRecordCreate, ExamCreate, CourseCreate, AssignmentCreate,
    NoteCreate, LinkCreate, KnowledgeItemCreate, ObjectiveCreate,
    ValidationError, validate_and_sanitize_input
)
from backup_manager import get_backup_manager

logger = logging.getLogger(__name__)


class DatabaseImprovements:
    """
    Classe mixin pour améliorer la classe Database existante
    Ajoute validation, gestion d'erreurs améliorée, et optimisations
    """
    
    def __init__(self, db_instance):
        """
        Initialise les améliorations avec une instance de Database
        
        Args:
            db_instance: Instance de la classe Database
        """
        self.db = db_instance
        self.backup_manager = get_backup_manager()
        self._setup_backup_manager()
        self._create_indexes()
    
    def _setup_backup_manager(self):
        """Configure le gestionnaire de backup"""
        def get_all_data():
            """Callback pour récupérer toutes les données"""
            try:
                events = self.db.get_all_events()
                return {'events': events}
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des données pour backup: {e}")
                return {'events': []}
        
        self.backup_manager.set_data_callback(get_all_data)
        if not self.backup_manager._running:
            self.backup_manager.start()
    
    def _create_indexes(self):
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
            "CREATE INDEX IF NOT EXISTS idx_links_category ON links(category)",
        ]
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                logger.debug(f"Index créé/vérifié: {index_sql.split('ON')[1].strip()}")
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'index: {e}")
        
        conn.commit()
        logger.info("Index de base de données créés/vérifiés")
    
    # ============================================================================
    # MÉTHODES AMÉLIORÉES AVEC VALIDATION
    # ============================================================================
    
    @handle_errors("Erreur lors de l'ajout d'événement")
    def add_event_validated(
        self,
        type: str,
        name: str,
        datetime_str: str,
        date_str: str,
        time_str: str,
        duration: int = 0,
        notes: str = ""
    ) -> int:
        """
        Ajoute un événement avec validation
        
        Args:
            type: Type d'événement
            name: Nom de l'événement
            datetime_str: Date et heure complète
            date_str: Date (YYYY-MM-DD)
            time_str: Heure (HH:MM)
            duration: Durée en minutes
            notes: Notes optionnelles
        
        Returns:
            ID de l'événement créé
        
        Raises:
            ValidationError: Si la validation échoue
            DatabaseError: Si l'insertion échoue
        """
        # Valider les données
        event_data = {
            'type': type,
            'name': name,
            'datetime_str': datetime_str,
            'date_str': date_str,
            'time_str': time_str,
            'duration': duration,
            'notes': notes
        }
        
        validated_data = validate_and_sanitize_input(event_data, EventCreate)
        
        # Ajouter l'événement
        event_id = self.db.add_event(
            type=validated_data['type'],
            name=validated_data['name'],
            datetime_str=validated_data['datetime_str'],
            date_str=validated_data['date_str'],
            time_str=validated_data['time_str'],
            duration=validated_data['duration'],
            notes=validated_data['notes']
        )
        
        # Demander un backup (pas immédiat pour les opérations normales)
        self.backup_manager.request_backup(immediate=False)
        
        return event_id
    
    @handle_errors("Erreur lors de l'ajout d'examen")
    def add_exam_validated(
        self,
        name: str,
        exam_date: str,
        subject: Optional[str] = None,
        exam_time: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None,
        reminder_days_before: int = 1
    ) -> int:
        """
        Ajoute un examen avec validation
        
        Args:
            name: Nom de l'examen
            exam_date: Date de l'examen (YYYY-MM-DD)
            subject: Matière (optionnel)
            exam_time: Heure de l'examen (HH:MM, optionnel)
            location: Lieu (optionnel)
            notes: Notes (optionnel)
            reminder_days_before: Nombre de jours avant pour le rappel
        
        Returns:
            ID de l'examen créé
        """
        exam_data = {
            'name': name,
            'exam_date': exam_date,
            'subject': subject,
            'exam_time': exam_time,
            'location': location,
            'notes': notes,
            'reminder_days_before': reminder_days_before
        }
        
        validated_data = validate_and_sanitize_input(exam_data, ExamCreate)
        
        exam_id = self.db.add_exam(
            name=validated_data['name'],
            exam_date=validated_data['exam_date'],
            subject=validated_data.get('subject'),
            exam_time=validated_data.get('exam_time'),
            location=validated_data.get('location'),
            notes=validated_data.get('notes'),
            reminder_days_before=validated_data['reminder_days_before']
        )
        
        self.backup_manager.request_backup(immediate=False)
        return exam_id
    
    @handle_errors("Erreur lors de l'ajout de cours")
    def add_course_validated(
        self,
        name: str,
        day_of_week: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        subject: Optional[str] = None,
        location: Optional[str] = None,
        teacher: Optional[str] = None,
        notes: Optional[str] = None,
        tupperware_reminder: int = 1
    ) -> int:
        """
        Ajoute un cours avec validation
        
        Args:
            name: Nom du cours
            day_of_week: Jour de la semaine (0-6)
            start_time: Heure de début (HH:MM)
            end_time: Heure de fin (HH:MM)
            subject: Matière
            location: Lieu
            teacher: Professeur
            notes: Notes
            tupperware_reminder: Rappel Tupperware (0 ou 1)
        
        Returns:
            ID du cours créé
        """
        course_data = {
            'name': name,
            'day_of_week': day_of_week,
            'start_time': start_time,
            'end_time': end_time,
            'subject': subject,
            'location': location,
            'teacher': teacher,
            'notes': notes,
            'tupperware_reminder': tupperware_reminder
        }
        
        validated_data = validate_and_sanitize_input(course_data, CourseCreate)
        
        course_id = self.db.add_course(
            name=validated_data['name'],
            day_of_week=validated_data.get('day_of_week'),
            start_time=validated_data.get('start_time'),
            end_time=validated_data.get('end_time'),
            subject=validated_data.get('subject'),
            location=validated_data.get('location'),
            teacher=validated_data.get('teacher'),
            notes=validated_data.get('notes'),
            tupperware_reminder=validated_data['tupperware_reminder']
        )
        
        self.backup_manager.request_backup(immediate=False)
        return course_id
    
    @handle_errors("Erreur lors de l'ajout de devoir")
    def add_assignment_validated(
        self,
        title: str,
        course_id: Optional[int] = None,
        due_date: Optional[str] = None,
        due_time: Optional[str] = None,
        description: Optional[str] = None,
        status: str = 'pending',
        priority: int = 3
    ) -> int:
        """
        Ajoute un devoir avec validation
        
        Args:
            title: Titre du devoir
            course_id: ID du cours associé
            due_date: Date d'échéance (YYYY-MM-DD)
            due_time: Heure d'échéance (HH:MM)
            description: Description
            status: Statut
            priority: Priorité (1-4)
        
        Returns:
            ID du devoir créé
        """
        assignment_data = {
            'title': title,
            'course_id': course_id,
            'due_date': due_date,
            'due_time': due_time,
            'description': description,
            'status': status,
            'priority': priority
        }
        
        validated_data = validate_and_sanitize_input(assignment_data, AssignmentCreate)
        
        assignment_id = self.db.add_assignment(
            title=validated_data['title'],
            course_id=validated_data.get('course_id'),
            due_date=validated_data.get('due_date'),
            due_time=validated_data.get('due_time'),
            description=validated_data.get('description'),
            status=validated_data['status'],
            priority=validated_data['priority']
        )
        
        self.backup_manager.request_backup(immediate=False)
        return assignment_id
    
    @handle_errors("Erreur lors de l'ajout de note")
    def add_note_validated(
        self,
        title: str,
        content: Optional[str] = None,
        tags: Optional[str] = None,
        category: Optional[str] = None
    ) -> int:
        """
        Ajoute une note avec validation
        
        Args:
            title: Titre de la note
            content: Contenu
            tags: Tags (séparés par virgules)
            category: Catégorie
        
        Returns:
            ID de la note créée
        """
        note_data = {
            'title': title,
            'content': content,
            'tags': tags,
            'category': category
        }
        
        validated_data = validate_and_sanitize_input(note_data, NoteCreate)
        
        note_id = self.db.add_note(
            title=validated_data['title'],
            content=validated_data.get('content'),
            tags=validated_data.get('tags'),
            category=validated_data.get('category')
        )
        
        self.backup_manager.request_backup(immediate=False)
        return note_id
    
    # ============================================================================
    # MÉTHODES DE RÉCUPÉRATION AMÉLIORÉES
    # ============================================================================
    
    @handle_errors("Erreur lors de la récupération de l'événement")
    def get_event_safe(self, event_id: int) -> Optional[Dict]:
        """
        Récupère un événement de manière sécurisée avec gestion d'erreurs
        
        Args:
            event_id: ID de l'événement
        
        Returns:
            Dictionnaire de l'événement ou None si non trouvé
        
        Raises:
            DatabaseNotFoundError: Si l'événement n'existe pas
        """
        try:
            events = self.db.get_all_events()
            for event in events:
                if event.get('id') == event_id:
                    return event
            
            raise DatabaseNotFoundError("Événement", event_id)
        except DatabaseNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur lors de la récupération de l'événement {event_id}", original_exception=e)
    
    @handle_errors("Erreur lors de la récupération des examens")
    def get_exams_safe(self, upcoming_only: bool = False) -> List[Dict]:
        """
        Récupère les examens de manière sécurisée
        
        Args:
            upcoming_only: Si True, retourne uniquement les examens à venir
        
        Returns:
            Liste des examens
        """
        try:
            return self.db.get_all_exams(upcoming_only=upcoming_only)
        except Exception as e:
            raise DatabaseError("Erreur lors de la récupération des examens", original_exception=e)
    
    # ============================================================================
    # MÉTHODES DE SUPPRESSION AMÉLIORÉES
    # ============================================================================
    
    @handle_errors("Erreur lors de la suppression")
    def delete_event_safe(self, event_id: int) -> bool:
        """
        Supprime un événement de manière sécurisée
        
        Args:
            event_id: ID de l'événement à supprimer
        
        Returns:
            True si la suppression a réussi
        
        Raises:
            DatabaseNotFoundError: Si l'événement n'existe pas
        """
        # Vérifier que l'événement existe
        event = self.get_event_safe(event_id)
        if not event:
            raise DatabaseNotFoundError("Événement", event_id)
        
        # Supprimer
        try:
            self.db.delete_event(event_id)
            self.backup_manager.request_backup(immediate=False)
            return True
        except Exception as e:
            raise DatabaseError(f"Erreur lors de la suppression de l'événement {event_id}", original_exception=e)
    
    # ============================================================================
    # MÉTHODES UTILITAIRES
    # ============================================================================
    
    def get_backup_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du système de backup
        
        Returns:
            Dictionnaire avec les informations du backup
        """
        return self.backup_manager.get_backup_info()
    
    def force_backup(self) -> bool:
        """
        Force un backup immédiat
        
        Returns:
            True si le backup a réussi
        """
        return self.backup_manager.force_backup_now()
    
    def cleanup(self):
        """Nettoie les ressources (arrête le backup manager)"""
        if self.backup_manager:
            self.backup_manager.stop()
