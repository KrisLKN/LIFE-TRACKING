"""
Modèles de données et structures pour l'application
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Exercise:
    """Modèle pour un exercice de musculation"""
    name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    rest_seconds: Optional[int] = None
    exercise_order: int = 0


@dataclass
class CardioActivity:
    """Modèle pour une activité cardio"""
    activity_type: str
    duration: Optional[int] = None  # en minutes
    distance: Optional[float] = None  # en km
    calories: Optional[int] = None


@dataclass
class SportSession:
    """Modèle pour une séance de sport complète"""
    session_type: Optional[str] = None
    total_duration: Optional[int] = None  # en minutes
    calories_burned: Optional[int] = None
    exercises: List[Exercise] = None
    cardio_activities: List[CardioActivity] = None
    
    def __post_init__(self):
        if self.exercises is None:
            self.exercises = []
        if self.cardio_activities is None:
            self.cardio_activities = []


@dataclass
class Meal:
    """Modèle pour un repas"""
    name: Optional[str] = None
    calories: Optional[int] = None
    protein: Optional[float] = None  # en grammes
    carbs: Optional[float] = None  # en grammes
    fats: Optional[float] = None  # en grammes


@dataclass
class SleepRecord:
    """Modèle pour un enregistrement de sommeil"""
    bedtime: Optional[str] = None  # format HH:MM
    wake_time: Optional[str] = None  # format HH:MM
    duration_hours: Optional[float] = None
    quality_score: Optional[int] = None  # 1-5


@dataclass
class WeightRecord:
    """Modèle pour un enregistrement de poids"""
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None
    muscle_mass_percent: Optional[float] = None


@dataclass
class WorkSession:
    """Modèle pour une session de travail"""
    task_type: Optional[str] = None
    productivity_score: Optional[int] = None  # 1-5


@dataclass
class Objective:
    """Modèle pour un objectif"""
    type: str
    name: str
    target_value: float
    current_value: float = 0.0
    deadline: Optional[str] = None
    frequency: Optional[str] = None
    status: str = 'active'


@dataclass
class Reminder:
    """Modèle pour un rappel"""
    type: str
    message: str
    time: str  # format HH:MM
    frequency: str
    enabled: bool = True


@dataclass
class Event:
    """Modèle pour un événement générique"""
    type: str
    name: str
    datetime: datetime
    duration: int = 0  # en minutes
    notes: Optional[str] = None
    
    # Données spécifiques selon le type
    sport_data: Optional[SportSession] = None
    meal_data: Optional[Meal] = None
    sleep_data: Optional[SleepRecord] = None
    weight_data: Optional[WeightRecord] = None
    hydration_data: Optional[float] = None  # en litres
    work_data: Optional[WorkSession] = None
    
    @property
    def date(self) -> str:
        """Retourne la date au format ISO"""
        return self.datetime.date().isoformat()
    
    @property
    def time(self) -> str:
        """Retourne l'heure au format HH:MM"""
        return self.datetime.time().strftime("%H:%M")
    
    @property
    def datetime_iso(self) -> str:
        """Retourne le datetime au format ISO"""
        return self.datetime.isoformat()
