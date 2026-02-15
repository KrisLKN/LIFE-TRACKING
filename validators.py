"""
Système de validation robuste pour toutes les entrées utilisateur
Utilise Pydantic pour une validation stricte et des messages d'erreur clairs
"""
from pydantic import BaseModel, Field, validator, HttpUrl, EmailStr
from typing import Optional, List
from datetime import datetime, date, time
import re
from config import (
    EVENT_TYPES, SPORT_SESSION_TYPES, CARDIO_TYPES,
    ASSIGNMENT_STATUS, PRIORITIES, SECOND_BRAIN_CATEGORIES,
    KNOWLEDGE_TYPES, OBJECTIVE_TYPES, OBJECTIVE_FREQUENCIES
)


class ValidationError(Exception):
    """Exception personnalisée pour les erreurs de validation"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


# ============================================================================
# VALIDATEURS D'ÉVÉNEMENTS
# ============================================================================

class EventCreate(BaseModel):
    """Modèle de validation pour la création d'événements"""
    type: str = Field(..., min_length=1, max_length=100, description="Type d'événement")
    name: str = Field(..., min_length=1, max_length=200, description="Nom de l'événement")
    datetime_str: str = Field(..., description="Date et heure complète")
    date_str: str = Field(..., description="Date (YYYY-MM-DD)")
    time_str: str = Field(..., description="Heure (HH:MM)")
    duration: int = Field(default=0, ge=0, le=1440, description="Durée en minutes (max 24h)")
    notes: Optional[str] = Field(default="", max_length=5000, description="Notes optionnelles")
    
    @validator('type')
    def validate_type(cls, v):
        """Valide que le type d'événement est autorisé"""
        allowed_keywords = ['Sport', 'Repas', 'Sommeil', 'Poids', 'Hydratation', 'Travail', 'Étude', 'Loisir', 'Social']
        if not any(keyword in v for keyword in allowed_keywords):
            raise ValueError(
                f"Type d'événement invalide: '{v}'. "
                f"Types autorisés: {', '.join(allowed_keywords)}"
            )
        return v.strip()
    
    @validator('name')
    def validate_name(cls, v):
        """Valide et nettoie le nom"""
        v = v.strip()
        if not v:
            raise ValueError("Le nom ne peut pas être vide")
        # Protection contre XSS basique
        if '<script' in v.lower() or 'javascript:' in v.lower():
            raise ValueError("Le nom contient des caractères non autorisés")
        return v
    
    @validator('date_str')
    def validate_date(cls, v):
        """Valide le format de date"""
        try:
            parsed_date = datetime.strptime(v, '%Y-%m-%d').date()
            # Permettre les dates passées (pour historique) mais pas trop anciennes
            min_date = date(2000, 1, 1)
            max_date = date(2100, 12, 31)
            if parsed_date < min_date or parsed_date > max_date:
                raise ValueError(f"La date doit être entre {min_date} et {max_date}")
            return v
        except ValueError as e:
            if 'does not match format' in str(e) or 'invalid' in str(e).lower():
                raise ValueError('Format de date invalide. Utilisez YYYY-MM-DD (ex: 2024-01-15)')
            raise
    
    @validator('time_str')
    def validate_time(cls, v):
        """Valide le format d'heure"""
        try:
            parsed_time = datetime.strptime(v, '%H:%M').time()
            return v
        except ValueError:
            raise ValueError('Format d\'heure invalide. Utilisez HH:MM (ex: 14:30)')
    
    @validator('datetime_str')
    def validate_datetime(cls, v, values):
        """Valide la cohérence entre date et datetime"""
        if 'date_str' in values and 'time_str' in values:
            expected_datetime = f"{values['date_str']} {values['time_str']}"
            if v != expected_datetime:
                # Vérifier si c'est juste un format différent mais valide
                try:
                    datetime.strptime(v, '%Y-%m-%d %H:%M')
                except ValueError:
                    raise ValueError('Format datetime invalide. Utilisez YYYY-MM-DD HH:MM')
        return v
    
    @validator('notes')
    def sanitize_notes(cls, v):
        """Nettoie les notes pour éviter XSS"""
        if v:
            # Supprimer les balises HTML dangereuses
            v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.IGNORECASE | re.DOTALL)
            v = re.sub(r'javascript:', '', v, flags=re.IGNORECASE)
        return v
    
    class Config:
        """Configuration Pydantic"""
        validate_assignment = True
        use_enum_values = True


# ============================================================================
# VALIDATEURS SPORT
# ============================================================================

class SportSessionCreate(BaseModel):
    """Validation pour une séance de sport"""
    event_id: int = Field(..., gt=0, description="ID de l'événement parent")
    session_type: Optional[str] = Field(None, max_length=100, description="Type de séance")
    total_duration: Optional[int] = Field(None, ge=0, le=1440, description="Durée totale en minutes")
    calories_burned: Optional[int] = Field(None, ge=0, le=10000, description="Calories brûlées")
    
    @validator('session_type')
    def validate_session_type(cls, v):
        """Valide le type de séance"""
        if v and v not in SPORT_SESSION_TYPES:
            raise ValueError(f"Type de séance invalide. Types autorisés: {', '.join(SPORT_SESSION_TYPES)}")
        return v


class ExerciseCreate(BaseModel):
    """Validation pour un exercice"""
    session_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=200)
    sets: Optional[int] = Field(None, ge=0, le=100)
    reps: Optional[int] = Field(None, ge=0, le=10000)
    weight: Optional[float] = Field(None, ge=0, le=1000)  # kg
    rest_seconds: Optional[int] = Field(None, ge=0, le=3600)  # max 1h de repos
    exercise_order: int = Field(default=0, ge=0)


class CardioActivityCreate(BaseModel):
    """Validation pour une activité cardio"""
    session_id: int = Field(..., gt=0)
    activity_type: Optional[str] = Field(None, max_length=100)
    duration: Optional[int] = Field(None, ge=0, le=1440)
    distance: Optional[float] = Field(None, ge=0, le=1000)  # km
    calories: Optional[int] = Field(None, ge=0, le=10000)
    
    @validator('activity_type')
    def validate_activity_type(cls, v):
        """Valide le type d'activité cardio"""
        if v and v not in CARDIO_TYPES:
            raise ValueError(f"Type d'activité cardio invalide. Types autorisés: {', '.join(CARDIO_TYPES)}")
        return v


# ============================================================================
# VALIDATEURS NUTRITION
# ============================================================================

class MealCreate(BaseModel):
    """Validation pour un repas"""
    event_id: int = Field(..., gt=0)
    name: Optional[str] = Field(None, max_length=200)
    calories: Optional[int] = Field(None, ge=0, le=10000)
    protein: Optional[float] = Field(None, ge=0, le=1000)  # grammes
    carbs: Optional[float] = Field(None, ge=0, le=1000)
    fats: Optional[float] = Field(None, ge=0, le=1000)


# ============================================================================
# VALIDATEURS SOMMEIL
# ============================================================================

class SleepRecordCreate(BaseModel):
    """Validation pour un enregistrement de sommeil"""
    event_id: int = Field(..., gt=0)
    bedtime: Optional[str] = Field(None, description="Heure de coucher (HH:MM)")
    wake_time: Optional[str] = Field(None, description="Heure de réveil (HH:MM)")
    duration_hours: Optional[float] = Field(None, ge=0, le=24, description="Durée en heures")
    quality_score: Optional[int] = Field(None, ge=1, le=10, description="Score de qualité (1-10)")
    
    @validator('bedtime', 'wake_time')
    def validate_time_format(cls, v):
        """Valide le format d'heure"""
        if v:
            try:
                datetime.strptime(v, '%H:%M')
            except ValueError:
                raise ValueError('Format d\'heure invalide. Utilisez HH:MM')
        return v
    
    @validator('duration_hours')
    def validate_duration(cls, v, values):
        """Valide la cohérence de la durée"""
        if v and 'bedtime' in values and 'wake_time' in values:
            if values['bedtime'] and values['wake_time']:
                # Calculer la durée réelle et comparer
                try:
                    bed = datetime.strptime(values['bedtime'], '%H:%M').time()
                    wake = datetime.strptime(values['wake_time'], '%H:%M').time()
                    # Logique de calcul simplifiée (ne gère pas le passage de minuit)
                    bed_minutes = bed.hour * 60 + bed.minute
                    wake_minutes = wake.hour * 60 + wake.minute
                    if wake_minutes < bed_minutes:
                        wake_minutes += 24 * 60  # Passage de minuit
                    calculated_hours = (wake_minutes - bed_minutes) / 60
                    if abs(calculated_hours - v) > 1:  # Tolérance de 1h
                        raise ValueError(
                            f"La durée ({v}h) ne correspond pas aux heures de coucher/réveil. "
                            f"Durée calculée: {calculated_hours:.1f}h"
                        )
                except (ValueError, KeyError):
                    pass  # Ignorer si les heures ne sont pas valides
        return v


# ============================================================================
# VALIDATEURS EXAMENS
# ============================================================================

class ExamCreate(BaseModel):
    """Validation pour un examen"""
    name: str = Field(..., min_length=1, max_length=200)
    subject: Optional[str] = Field(None, max_length=100)
    exam_date: str = Field(..., description="Date de l'examen (YYYY-MM-DD)")
    exam_time: Optional[str] = Field(None, description="Heure de l'examen (HH:MM)")
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=2000)
    reminder_days_before: int = Field(default=1, ge=0, le=30)
    
    @validator('name')
    def validate_name(cls, v):
        """Valide le nom de l'examen"""
        v = v.strip()
        if not v:
            raise ValueError("Le nom de l'examen ne peut pas être vide")
        return v
    
    @validator('exam_date')
    def validate_exam_date(cls, v):
        """Valide la date d'examen"""
        try:
            exam_date = datetime.strptime(v, '%Y-%m-%d').date()
            today = datetime.now().date()
            # Permettre les examens passés (pour historique) mais pas trop anciens
            min_date = date(2000, 1, 1)
            if exam_date < min_date:
                raise ValueError(f"La date ne peut pas être antérieure à {min_date}")
            return v
        except ValueError as e:
            if 'does not match format' in str(e) or 'invalid' in str(e).lower():
                raise ValueError('Format de date invalide. Utilisez YYYY-MM-DD')
            raise
    
    @validator('exam_time')
    def validate_exam_time(cls, v):
        """Valide l'heure de l'examen"""
        if v:
            try:
                datetime.strptime(v, '%H:%M')
            except ValueError:
                raise ValueError('Format d\'heure invalide. Utilisez HH:MM')
        return v


# ============================================================================
# VALIDATEURS COURS
# ============================================================================

class CourseCreate(BaseModel):
    """Validation pour un cours"""
    name: str = Field(..., min_length=1, max_length=200)
    subject: Optional[str] = Field(None, max_length=100)
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="0=Lundi, 6=Dimanche")
    start_time: Optional[str] = Field(None, description="Heure de début (HH:MM)")
    end_time: Optional[str] = Field(None, description="Heure de fin (HH:MM)")
    location: Optional[str] = Field(None, max_length=200)
    teacher: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=2000)
    tupperware_reminder: int = Field(default=1, ge=0, le=1, description="Rappel Tupperware (0 ou 1)")
    
    @validator('name')
    def validate_name(cls, v):
        """Valide le nom du cours"""
        v = v.strip()
        if not v:
            raise ValueError("Le nom du cours ne peut pas être vide")
        return v
    
    @validator('start_time', 'end_time')
    def validate_time(cls, v):
        """Valide le format d'heure"""
        if v:
            try:
                datetime.strptime(v, '%H:%M')
            except ValueError:
                raise ValueError('Format d\'heure invalide. Utilisez HH:MM')
        return v
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        """Valide que l'heure de fin est après l'heure de début"""
        if v and 'start_time' in values and values['start_time']:
            try:
                start = datetime.strptime(values['start_time'], '%H:%M').time()
                end = datetime.strptime(v, '%H:%M').time()
                if end <= start:
                    raise ValueError("L'heure de fin doit être après l'heure de début")
            except ValueError as e:
                if 'Format' in str(e):
                    raise
                raise ValueError("L'heure de fin doit être après l'heure de début")
        return v


# ============================================================================
# VALIDATEURS DEVOIRS
# ============================================================================

class AssignmentCreate(BaseModel):
    """Validation pour un devoir"""
    title: str = Field(..., min_length=1, max_length=200)
    course_id: Optional[int] = Field(None, gt=0)
    due_date: Optional[str] = Field(None, description="Date d'échéance (YYYY-MM-DD)")
    due_time: Optional[str] = Field(None, description="Heure d'échéance (HH:MM)")
    description: Optional[str] = Field(None, max_length=5000)
    status: str = Field(default='pending', description="Statut du devoir")
    priority: int = Field(default=3, ge=1, le=4, description="Priorité (1-4)")
    
    @validator('title')
    def validate_title(cls, v):
        """Valide le titre"""
        v = v.strip()
        if not v:
            raise ValueError("Le titre ne peut pas être vide")
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Valide le statut"""
        if v not in ASSIGNMENT_STATUS:
            raise ValueError(f"Statut invalide. Statuts autorisés: {', '.join(ASSIGNMENT_STATUS)}")
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v):
        """Valide la date d'échéance"""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('Format de date invalide. Utilisez YYYY-MM-DD')
        return v
    
    @validator('due_time')
    def validate_due_time(cls, v):
        """Valide l'heure d'échéance"""
        if v:
            try:
                datetime.strptime(v, '%H:%M')
            except ValueError:
                raise ValueError('Format d\'heure invalide. Utilisez HH:MM')
        return v


# ============================================================================
# VALIDATEURS SECOND CERVEAU
# ============================================================================

class NoteCreate(BaseModel):
    """Validation pour une note"""
    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = Field(None, max_length=50000)
    tags: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    
    @validator('title')
    def validate_title(cls, v):
        """Valide le titre"""
        v = v.strip()
        if not v:
            raise ValueError("Le titre ne peut pas être vide")
        return v
    
    @validator('category')
    def validate_category(cls, v):
        """Valide la catégorie"""
        if v and v not in SECOND_BRAIN_CATEGORIES:
            raise ValueError(f"Catégorie invalide. Catégories autorisées: {', '.join(SECOND_BRAIN_CATEGORIES)}")
        return v


class LinkCreate(BaseModel):
    """Validation pour un lien"""
    title: str = Field(..., min_length=1, max_length=200)
    url: HttpUrl = Field(..., description="URL valide")
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    note_id: Optional[int] = Field(None, gt=0)
    
    @validator('title')
    def validate_title(cls, v):
        """Valide le titre"""
        v = v.strip()
        if not v:
            raise ValueError("Le titre ne peut pas être vide")
        return v


class KnowledgeItemCreate(BaseModel):
    """Validation pour un élément de connaissance"""
    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = Field(None, max_length=50000)
    type: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    related_items: Optional[str] = Field(None, max_length=1000)
    
    @validator('title')
    def validate_title(cls, v):
        """Valide le titre"""
        v = v.strip()
        if not v:
            raise ValueError("Le titre ne peut pas être vide")
        return v
    
    @validator('type')
    def validate_type(cls, v):
        """Valide le type"""
        if v and v not in KNOWLEDGE_TYPES:
            raise ValueError(f"Type invalide. Types autorisés: {', '.join(KNOWLEDGE_TYPES)}")
        return v


# ============================================================================
# VALIDATEURS OBJECTIFS
# ============================================================================

class ObjectiveCreate(BaseModel):
    """Validation pour un objectif"""
    type: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    target_value: float = Field(..., ge=0, description="Valeur cible")
    deadline: Optional[str] = Field(None, description="Date limite (YYYY-MM-DD)")
    frequency: Optional[str] = Field(None, max_length=50)
    
    @validator('name')
    def validate_name(cls, v):
        """Valide le nom"""
        v = v.strip()
        if not v:
            raise ValueError("Le nom ne peut pas être vide")
        return v
    
    @validator('type')
    def validate_type(cls, v):
        """Valide le type d'objectif"""
        if v not in OBJECTIVE_TYPES:
            raise ValueError(f"Type d'objectif invalide. Types autorisés: {', '.join(OBJECTIVE_TYPES)}")
        return v
    
    @validator('frequency')
    def validate_frequency(cls, v):
        """Valide la fréquence"""
        if v and v not in OBJECTIVE_FREQUENCIES:
            raise ValueError(f"Fréquence invalide. Fréquences autorisées: {', '.join(OBJECTIVE_FREQUENCIES)}")
        return v
    
    @validator('deadline')
    def validate_deadline(cls, v):
        """Valide la date limite"""
        if v:
            try:
                deadline_date = datetime.strptime(v, '%Y-%m-%d').date()
                today = datetime.now().date()
                if deadline_date < today:
                    raise ValueError("La date limite ne peut pas être dans le passé")
            except ValueError as e:
                if 'does not match format' in str(e) or 'invalid' in str(e).lower():
                    raise ValueError('Format de date invalide. Utilisez YYYY-MM-DD')
                raise
        return v


# ============================================================================
# FONCTIONS UTILITAIRES DE VALIDATION
# ============================================================================

def validate_and_sanitize_input(data: dict, model_class: type[BaseModel]) -> dict:
    """
    Valide et nettoie les données d'entrée
    
    Args:
        data: Dictionnaire de données à valider
        model_class: Classe Pydantic à utiliser pour la validation
    
    Returns:
        Dictionnaire validé et nettoyé
    
    Raises:
        ValidationError: Si la validation échoue
    """
    try:
        instance = model_class(**data)
        return instance.dict(exclude_none=False)
    except Exception as e:
        # Convertir les erreurs Pydantic en ValidationError personnalisée
        error_messages = []
        if hasattr(e, 'errors'):
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                message = error['msg']
                error_messages.append(f"{field}: {message}")
        else:
            error_messages.append(str(e))
        
        raise ValidationError(
            message="Erreurs de validation:\n" + "\n".join(error_messages),
            field=None
        )


def validate_date_string(date_str: str) -> date:
    """Valide et parse une chaîne de date"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationError(f"Format de date invalide: {date_str}. Utilisez YYYY-MM-DD")


def validate_time_string(time_str: str) -> time:
    """Valide et parse une chaîne d'heure"""
    try:
        return datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        raise ValidationError(f"Format d'heure invalide: {time_str}. Utilisez HH:MM")


def sanitize_text(text: str, max_length: int = None) -> str:
    """
    Nettoie un texte pour éviter XSS et autres problèmes
    
    Args:
        text: Texte à nettoyer
        max_length: Longueur maximale autorisée
    
    Returns:
        Texte nettoyé
    """
    if not text:
        return ""
    
    # Supprimer les balises HTML dangereuses
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)  # Supprimer les event handlers
    
    # Limiter la longueur
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()
