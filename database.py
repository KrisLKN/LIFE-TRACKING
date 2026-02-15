"""
Module de gestion de la base de données SQLite avec backup JSON automatique
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

# Configuration
DB_FILE = "tracker.db"
JSON_BACKUP_FILE = "events_data.json"

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Classe pour gérer la base de données SQLite et les backups JSON"""
    
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self.conn = None
        self.init_database()
        self.migrate_from_json()
    
    def get_connection(self):
        """Obtient une connexion à la base de données"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_database(self):
        """Initialise toutes les tables de la base de données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table principale des événements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                datetime TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                duration INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des séances de sport
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sport_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                session_type TEXT,
                total_duration INTEGER,
                calories_burned INTEGER,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            )
        """)
        
        # Table des exercices
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                sets INTEGER,
                reps INTEGER,
                weight REAL,
                rest_seconds INTEGER,
                exercise_order INTEGER,
                FOREIGN KEY (session_id) REFERENCES sport_sessions(id) ON DELETE CASCADE
            )
        """)
        
        # Table des activités cardio
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cardio_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                activity_type TEXT,
                duration INTEGER,
                distance REAL,
                calories INTEGER,
                FOREIGN KEY (session_id) REFERENCES sport_sessions(id) ON DELETE CASCADE
            )
        """)
        
        # Table des repas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                name TEXT,
                calories INTEGER,
                protein REAL,
                carbs REAL,
                fats REAL,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            )
        """)
        
        # Table des enregistrements de sommeil
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sleep_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                bedtime TEXT,
                wake_time TEXT,
                duration_hours REAL,
                quality_score INTEGER,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            )
        """)
        
        # Table des enregistrements de poids
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weight_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                weight_kg REAL,
                body_fat_percent REAL,
                muscle_mass_percent REAL,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            )
        """)
        
        # Table des enregistrements d'hydratation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hydration_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                amount_liters REAL,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            )
        """)
        
        # Table des sessions de travail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                task_type TEXT,
                productivity_score INTEGER,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            )
        """)
        
        # Table des objectifs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS objectives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                target_value REAL,
                current_value REAL DEFAULT 0,
                deadline TEXT,
                frequency TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des rappels
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                message TEXT,
                time TEXT,
                frequency TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des examens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT,
                exam_date TEXT NOT NULL,
                exam_time TEXT,
                location TEXT,
                notes TEXT,
                reminder_days_before INTEGER DEFAULT 1,
                notification_sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des cours
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT,
                day_of_week INTEGER,
                start_time TEXT,
                end_time TEXT,
                location TEXT,
                teacher TEXT,
                notes TEXT,
                tupperware_reminder INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des devoirs/assignments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course_id INTEGER,
                due_date TEXT,
                due_time TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 3,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des notes (Second Cerveau)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                tags TEXT,
                category TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des liens/ressources
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                category TEXT,
                note_id INTEGER,
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE SET NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des éléments de connaissance (Second Cerveau)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                type TEXT,
                tags TEXT,
                related_items TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des rappels intelligents
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smart_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_id INTEGER,
                reminder_type TEXT,
                reminder_time TEXT,
                message TEXT,
                notification_method TEXT,
                sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table de l'historique des notifications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL,
                recipient TEXT,
                subject TEXT,
                message TEXT,
                method TEXT,
                status TEXT,
                sent_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Base de données initialisée avec succès")
    
    def migrate_from_json(self):
        """Migre les données depuis le fichier JSON existant vers SQLite"""
        if not os.path.exists(JSON_BACKUP_FILE):
            return
        
        try:
            with open(JSON_BACKUP_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            events = data.get('events', [])
            if not events:
                return
            
            # Vérifier si des données existent déjà
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            count = cursor.fetchone()[0]
            
            if count > 0:
                logger.info("Des données existent déjà dans la base, migration ignorée")
                return
            
            # Migrer les événements
            for event in events:
                event_id = self.add_event(
                    type=event.get('type', ''),
                    name=event.get('name', ''),
                    datetime_str=event.get('datetime', ''),
                    date_str=event.get('date', ''),
                    time_str=event.get('time', ''),
                    duration=event.get('duration', 0),
                    notes=event.get('notes', '')
                )
            
            logger.info(f"Migration réussie : {len(events)} événements migrés")
        except Exception as e:
            logger.error(f"Erreur lors de la migration : {e}")
    
    def add_event(self, type: str, name: str, datetime_str: str, date_str: str, 
                  time_str: str, duration: int = 0, notes: str = "") -> int:
        """Ajoute un événement et retourne son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events (type, name, datetime, date, time, duration, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (type, name, datetime_str, date_str, time_str, duration, notes))
        
        event_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return event_id
    
    def add_sport_session(self, event_id: int, session_type: str = None, 
                         total_duration: int = None, calories_burned: int = None) -> int:
        """Ajoute une séance de sport et retourne son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sport_sessions (event_id, session_type, total_duration, calories_burned)
            VALUES (?, ?, ?, ?)
        """, (event_id, session_type, total_duration, calories_burned))
        
        session_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return session_id
    
    def add_exercise(self, session_id: int, name: str, sets: int = None, 
                    reps: int = None, weight: float = None, 
                    rest_seconds: int = None, exercise_order: int = 0) -> int:
        """Ajoute un exercice à une séance de sport"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO exercises (session_id, name, sets, reps, weight, rest_seconds, exercise_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, name, sets, reps, weight, rest_seconds, exercise_order))
        
        exercise_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return exercise_id
    
    def add_cardio_activity(self, session_id: int, activity_type: str = None,
                           duration: int = None, distance: float = None,
                           calories: int = None) -> int:
        """Ajoute une activité cardio à une séance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO cardio_activities (session_id, activity_type, duration, distance, calories)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, activity_type, duration, distance, calories))
        
        activity_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return activity_id
    
    def add_meal(self, event_id: int, name: str = None, calories: int = None,
                protein: float = None, carbs: float = None, fats: float = None) -> int:
        """Ajoute un repas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO meals (event_id, name, calories, protein, carbs, fats)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event_id, name, calories, protein, carbs, fats))
        
        meal_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return meal_id
    
    def add_sleep_record(self, event_id: int, bedtime: str = None, wake_time: str = None,
                        duration_hours: float = None, quality_score: int = None) -> int:
        """Ajoute un enregistrement de sommeil"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sleep_records (event_id, bedtime, wake_time, duration_hours, quality_score)
            VALUES (?, ?, ?, ?, ?)
        """, (event_id, bedtime, wake_time, duration_hours, quality_score))
        
        sleep_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return sleep_id
    
    def add_weight_record(self, event_id: int, weight_kg: float = None,
                         body_fat_percent: float = None, 
                         muscle_mass_percent: float = None) -> int:
        """Ajoute un enregistrement de poids"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO weight_records (event_id, weight_kg, body_fat_percent, muscle_mass_percent)
            VALUES (?, ?, ?, ?)
        """, (event_id, weight_kg, body_fat_percent, muscle_mass_percent))
        
        weight_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return weight_id
    
    def add_hydration_record(self, event_id: int, amount_liters: float) -> int:
        """Ajoute un enregistrement d'hydratation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO hydration_records (event_id, amount_liters)
            VALUES (?, ?)
        """, (event_id, amount_liters))
        
        hydration_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return hydration_id
    
    def add_work_session(self, event_id: int, task_type: str = None,
                        productivity_score: int = None) -> int:
        """Ajoute une session de travail"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO work_sessions (event_id, task_type, productivity_score)
            VALUES (?, ?, ?)
        """, (event_id, task_type, productivity_score))
        
        work_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return work_id
    
    def get_all_events(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Récupère tous les événements avec filtres optionnels"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('type'):
                query += " AND type LIKE ?"
                params.append(f"%{filters['type']}%")
            if filters.get('date_from'):
                query += " AND date >= ?"
                params.append(filters['date_from'])
            if filters.get('date_to'):
                query += " AND date <= ?"
                params.append(filters['date_to'])
        
        query += " ORDER BY datetime DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            event = dict(row)
            # Charger les données associées selon le type
            event_id = event['id']
            event_type = event['type']
            
            if 'Sport' in event_type:
                event['sport_data'] = self.get_sport_session_data(event_id)
            elif 'Repas' in event_type or '🍽️' in event_type:
                event['meal_data'] = self.get_meal_data(event_id)
            elif 'Sommeil' in event_type or '😴' in event_type:
                event['sleep_data'] = self.get_sleep_data(event_id)
            elif 'Poids' in event_type:
                event['weight_data'] = self.get_weight_data(event_id)
            elif 'Hydratation' in event_type or '💧' in event_type:
                event['hydration_data'] = self.get_hydration_data(event_id)
            elif 'Travail' in event_type or '💼' in event_type:
                event['work_data'] = self.get_work_data(event_id)
            
            events.append(event)
        
        return events
    
    def get_sport_session_data(self, event_id: int) -> Optional[Dict]:
        """Récupère les données d'une séance de sport"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sport_sessions WHERE event_id = ?", (event_id,))
        session = cursor.fetchone()
        
        if not session:
            return None
        
        session_dict = dict(session)
        session_id = session_dict['id']
        
        # Récupérer les exercices
        cursor.execute("""
            SELECT * FROM exercises WHERE session_id = ?
            ORDER BY exercise_order
        """, (session_id,))
        exercises = [dict(row) for row in cursor.fetchall()]
        session_dict['exercises'] = exercises
        
        # Récupérer les activités cardio
        cursor.execute("SELECT * FROM cardio_activities WHERE session_id = ?", (session_id,))
        cardio = [dict(row) for row in cursor.fetchall()]
        session_dict['cardio'] = cardio
        
        return session_dict
    
    def get_meal_data(self, event_id: int) -> Optional[Dict]:
        """Récupère les données d'un repas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM meals WHERE event_id = ?", (event_id,))
        meal = cursor.fetchone()
        
        return dict(meal) if meal else None
    
    def get_sleep_data(self, event_id: int) -> Optional[Dict]:
        """Récupère les données de sommeil"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sleep_records WHERE event_id = ?", (event_id,))
        sleep = cursor.fetchone()
        
        return dict(sleep) if sleep else None
    
    def get_weight_data(self, event_id: int) -> Optional[Dict]:
        """Récupère les données de poids"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM weight_records WHERE event_id = ?", (event_id,))
        weight = cursor.fetchone()
        
        return dict(weight) if weight else None
    
    def get_hydration_data(self, event_id: int) -> Optional[Dict]:
        """Récupère les données d'hydratation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM hydration_records WHERE event_id = ?", (event_id,))
        hydration = cursor.fetchone()
        
        return dict(hydration) if hydration else None
    
    def get_work_data(self, event_id: int) -> Optional[Dict]:
        """Récupère les données de travail"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM work_sessions WHERE event_id = ?", (event_id,))
        work = cursor.fetchone()
        
        return dict(work) if work else None
    
    def delete_event(self, event_id: int):
        """Supprime un événement et toutes ses données associées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        self.backup_to_json()
    
    def add_objective(self, type: str, name: str, target_value: float,
                     deadline: str = None, frequency: str = None) -> int:
        """Ajoute un objectif"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO objectives (type, name, target_value, deadline, frequency)
            VALUES (?, ?, ?, ?, ?)
        """, (type, name, target_value, deadline, frequency))
        
        obj_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return obj_id
    
    def get_all_objectives(self, status: str = 'active') -> List[Dict]:
        """Récupère tous les objectifs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM objectives WHERE status = ? ORDER BY created_at DESC", (status,))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_objective(self, obj_id: int, current_value: float = None, status: str = None):
        """Met à jour un objectif"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if current_value is not None:
            updates.append("current_value = ?")
            params.append(current_value)
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if updates:
            params.append(obj_id)
            query = f"UPDATE objectives SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            self.backup_to_json()
    
    def add_reminder(self, type: str, message: str, time: str, frequency: str) -> int:
        """Ajoute un rappel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO reminders (type, message, time, frequency)
            VALUES (?, ?, ?, ?)
        """, (type, message, time, frequency))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return reminder_id
    
    def get_all_reminders(self, enabled_only: bool = True) -> List[Dict]:
        """Récupère tous les rappels"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if enabled_only:
            cursor.execute("SELECT * FROM reminders WHERE enabled = 1 ORDER BY time")
        else:
            cursor.execute("SELECT * FROM reminders ORDER BY time")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def toggle_reminder(self, reminder_id: int, enabled: bool):
        """Active/désactive un rappel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE reminders SET enabled = ? WHERE id = ?", (1 if enabled else 0, reminder_id))
        conn.commit()
        self.backup_to_json()
    
    def delete_reminder(self, reminder_id: int):
        """Supprime un rappel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        self.backup_to_json()
    
    def backup_to_json(self):
        """Crée un backup JSON de toutes les données"""
        try:
            events = self.get_all_events()
            
            # Convertir les Row objects en dicts simples
            events_data = []
            for event in events:
                event_dict = {
                    'id': event['id'],
                    'type': event['type'],
                    'name': event['name'],
                    'datetime': event['datetime'],
                    'date': event['date'],
                    'time': event['time'],
                    'duration': event['duration'],
                    'notes': event.get('notes', '')
                }
                
                # Ajouter les données spécifiques
                if 'sport_data' in event:
                    event_dict['sport_data'] = event['sport_data']
                if 'meal_data' in event:
                    event_dict['meal_data'] = event['meal_data']
                if 'sleep_data' in event:
                    event_dict['sleep_data'] = event['sleep_data']
                if 'weight_data' in event:
                    event_dict['weight_data'] = event['weight_data']
                if 'hydration_data' in event:
                    event_dict['hydration_data'] = event['hydration_data']
                if 'work_data' in event:
                    event_dict['work_data'] = event['work_data']
                
                events_data.append(event_dict)
            
            backup_data = {'events': events_data}
            
            with open(JSON_BACKUP_FILE, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info("Backup JSON créé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du backup JSON : {e}")
    
    # ==================== FONCTIONS EXAMENS ====================
    def add_exam(self, name: str, exam_date: str, subject: str = None, 
                 exam_time: str = None, location: str = None, notes: str = None,
                 reminder_days_before: int = 1) -> int:
        """Ajoute un examen"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO exams (name, subject, exam_date, exam_time, location, notes, reminder_days_before)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, subject, exam_date, exam_time, location, notes, reminder_days_before))
        
        exam_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return exam_id
    
    def get_all_exams(self, upcoming_only: bool = False) -> List[Dict]:
        """Récupère tous les examens"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if upcoming_only:
            today = datetime.now().date().isoformat()
            cursor.execute("SELECT * FROM exams WHERE exam_date >= ? ORDER BY exam_date, exam_time", (today,))
        else:
            cursor.execute("SELECT * FROM exams ORDER BY exam_date, exam_time")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_exams_by_date_range(self, date_from: str, date_to: str) -> List[Dict]:
        """Récupère les examens dans une plage de dates"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM exams 
            WHERE exam_date >= ? AND exam_date <= ?
            ORDER BY exam_date, exam_time
        """, (date_from, date_to))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_upcoming_exams(self, days: int = 30) -> List[Dict]:
        """Récupère les examens à venir dans les X prochains jours"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        future_date = (datetime.now().date() + timedelta(days=days)).isoformat()
        cursor.execute("""
            SELECT * FROM exams 
            WHERE exam_date >= ? AND exam_date <= ?
            ORDER BY exam_date, exam_time
        """, (today, future_date))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_exam(self, exam_id: int, name: str = None, subject: str = None,
                    exam_date: str = None, exam_time: str = None, location: str = None,
                    notes: str = None, reminder_days_before: int = None, notification_sent: int = None):
        """Met à jour un examen"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if subject is not None:
            updates.append("subject = ?")
            params.append(subject)
        if exam_date is not None:
            updates.append("exam_date = ?")
            params.append(exam_date)
        if exam_time is not None:
            updates.append("exam_time = ?")
            params.append(exam_time)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if reminder_days_before is not None:
            updates.append("reminder_days_before = ?")
            params.append(reminder_days_before)
        if notification_sent is not None:
            updates.append("notification_sent = ?")
            params.append(notification_sent)
        
        if updates:
            params.append(exam_id)
            query = f"UPDATE exams SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            self.backup_to_json()
    
    def delete_exam(self, exam_id: int):
        """Supprime un examen"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
        conn.commit()
        self.backup_to_json()
    
    # ==================== FONCTIONS COURS ====================
    def add_course(self, name: str, day_of_week: int = None, start_time: str = None,
                   end_time: str = None, subject: str = None, location: str = None,
                   teacher: str = None, notes: str = None, tupperware_reminder: int = 1) -> int:
        """Ajoute un cours"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO courses (name, subject, day_of_week, start_time, end_time, 
                               location, teacher, notes, tupperware_reminder)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, subject, day_of_week, start_time, end_time, location, teacher, notes, tupperware_reminder))
        
        course_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return course_id
    
    def get_all_courses(self) -> List[Dict]:
        """Récupère tous les cours"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses ORDER BY day_of_week, start_time")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_courses_by_day(self, day_of_week: int) -> List[Dict]:
        """Récupère les cours d'un jour spécifique (0=lundi, 6=dimanche)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses WHERE day_of_week = ? ORDER BY start_time", (day_of_week,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_courses_for_week(self) -> Dict[int, List[Dict]]:
        """Récupère tous les cours organisés par jour de la semaine"""
        all_courses = self.get_all_courses()
        courses_by_day = {}
        for course in all_courses:
            day = course.get('day_of_week')
            if day is not None:
                if day not in courses_by_day:
                    courses_by_day[day] = []
                courses_by_day[day].append(course)
        return courses_by_day
    
    def update_course(self, course_id: int, name: str = None, day_of_week: int = None,
                      start_time: str = None, end_time: str = None, subject: str = None,
                      location: str = None, teacher: str = None, notes: str = None,
                      tupperware_reminder: int = None):
        """Met à jour un cours"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if day_of_week is not None:
            updates.append("day_of_week = ?")
            params.append(day_of_week)
        if start_time is not None:
            updates.append("start_time = ?")
            params.append(start_time)
        if end_time is not None:
            updates.append("end_time = ?")
            params.append(end_time)
        if subject is not None:
            updates.append("subject = ?")
            params.append(subject)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if teacher is not None:
            updates.append("teacher = ?")
            params.append(teacher)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if tupperware_reminder is not None:
            updates.append("tupperware_reminder = ?")
            params.append(tupperware_reminder)
        
        if updates:
            params.append(course_id)
            query = f"UPDATE courses SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            self.backup_to_json()
    
    def delete_course(self, course_id: int):
        """Supprime un cours"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        conn.commit()
        self.backup_to_json()
    
    # ==================== FONCTIONS DEVOIRS ====================
    def add_assignment(self, title: str, course_id: int = None, due_date: str = None,
                      due_time: str = None, description: str = None, 
                      status: str = 'pending', priority: int = 3) -> int:
        """Ajoute un devoir"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO assignments (title, course_id, due_date, due_time, description, status, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, course_id, due_date, due_time, description, status, priority))
        
        assignment_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return assignment_id
    
    def get_all_assignments(self, status: str = None) -> List[Dict]:
        """Récupère tous les devoirs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM assignments WHERE status = ? ORDER BY due_date, priority DESC", (status,))
        else:
            cursor.execute("SELECT * FROM assignments ORDER BY due_date, priority DESC")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_assignments_by_status(self, status: str) -> List[Dict]:
        """Récupère les devoirs par statut"""
        return self.get_all_assignments(status=status)
    
    def get_assignments_by_course(self, course_id: int) -> List[Dict]:
        """Récupère les devoirs d'un cours spécifique"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM assignments 
            WHERE course_id = ? 
            ORDER BY due_date, priority DESC
        """, (course_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_upcoming_assignments(self, days: int = 7) -> List[Dict]:
        """Récupère les devoirs à venir dans les X prochains jours"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        future_date = (datetime.now().date() + timedelta(days=days)).isoformat()
        cursor.execute("""
            SELECT * FROM assignments 
            WHERE due_date >= ? AND due_date <= ? AND status != 'completed'
            ORDER BY due_date, priority DESC
        """, (today, future_date))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_assignment(self, assignment_id: int, title: str = None, course_id: int = None,
                         due_date: str = None, due_time: str = None, description: str = None,
                         status: str = None, priority: int = None):
        """Met à jour un devoir"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if course_id is not None:
            updates.append("course_id = ?")
            params.append(course_id)
        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date)
        if due_time is not None:
            updates.append("due_time = ?")
            params.append(due_time)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        
        if updates:
            params.append(assignment_id)
            query = f"UPDATE assignments SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            self.backup_to_json()
    
    def update_assignment_status(self, assignment_id: int, status: str):
        """Met à jour le statut d'un devoir"""
        self.update_assignment(assignment_id, status=status)
    
    def delete_assignment(self, assignment_id: int):
        """Supprime un devoir"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        conn.commit()
        self.backup_to_json()
    
    # ==================== FONCTIONS SECOND CERVEAU - NOTES ====================
    def add_note(self, title: str, content: str = None, tags: str = None,
                category: str = None) -> int:
        """Ajoute une note"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO notes (title, content, tags, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, content, tags, category, now, now))
        
        note_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return note_id
    
    def update_note(self, note_id: int, title: str = None, content: str = None,
                        tags: str = None, category: str = None):
        """Met à jour une note"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(note_id)
            query = f"UPDATE notes SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            self.backup_to_json()
    
    def get_all_notes(self, category: str = None, tag: str = None) -> List[Dict]:
        """Récupère toutes les notes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute("SELECT * FROM notes WHERE category = ? ORDER BY updated_at DESC", (category,))
        elif tag:
            cursor.execute("SELECT * FROM notes WHERE tags LIKE ? ORDER BY updated_at DESC", (f"%{tag}%",))
        else:
            cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_notes(self, query: str) -> List[Dict]:
        """Recherche dans les notes par titre, contenu, tags ou catégorie"""
        conn = self.get_connection()
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT * FROM notes 
            WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? OR category LIKE ?
            ORDER BY updated_at DESC
        """, (search_term, search_term, search_term, search_term))
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_note(self, note_id: int):
        """Supprime une note"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        self.backup_to_json()
    
    # ==================== FONCTIONS LIENS ====================
    def add_link(self, title: str, url: str, description: str = None,
                tags: str = None, category: str = None, note_id: int = None) -> int:
        """Ajoute un lien"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO links (title, url, description, tags, category, note_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, url, description, tags, category, note_id))
        
        link_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return link_id
    
    def get_all_links(self, category: str = None) -> List[Dict]:
        """Récupère tous les liens"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute("SELECT * FROM links WHERE category = ? ORDER BY created_at DESC", (category,))
        else:
            cursor.execute("SELECT * FROM links ORDER BY created_at DESC")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_links_by_note(self, note_id: int) -> List[Dict]:
        """Récupère les liens associés à une note"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM links WHERE note_id = ? ORDER BY created_at DESC", (note_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_link(self, link_id: int, title: str = None, url: str = None,
                   description: str = None, tags: str = None, category: str = None,
                   note_id: int = None):
        """Met à jour un lien"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if url is not None:
            updates.append("url = ?")
            params.append(url)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if note_id is not None:
            updates.append("note_id = ?")
            params.append(note_id)
        
        if updates:
            params.append(link_id)
            query = f"UPDATE links SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            self.backup_to_json()
    
    def delete_link(self, link_id: int):
        """Supprime un lien"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM links WHERE id = ?", (link_id,))
        conn.commit()
        self.backup_to_json()
    
    # ==================== FONCTIONS CONNAISSANCES ====================
    def add_knowledge_item(self, title: str, content: str = None, type: str = None,
                          tags: str = None, related_items: str = None) -> int:
        """Ajoute un élément de connaissance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO knowledge_items (title, content, type, tags, related_items)
            VALUES (?, ?, ?, ?, ?)
        """, (title, content, type, tags, related_items))
        
        item_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return item_id
    
    def get_all_knowledge_items(self, type: str = None) -> List[Dict]:
        """Récupère tous les éléments de connaissance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if type:
            cursor.execute("SELECT * FROM knowledge_items WHERE type = ? ORDER BY updated_at DESC", (type,))
        else:
            cursor.execute("SELECT * FROM knowledge_items ORDER BY updated_at DESC")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_knowledge(self, query: str) -> List[Dict]:
        """Recherche dans les éléments de connaissance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT * FROM knowledge_items 
            WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? OR type LIKE ?
            ORDER BY updated_at DESC
        """, (search_term, search_term, search_term, search_term))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_knowledge_item(self, item_id: int, title: str = None, content: str = None,
                             type: str = None, tags: str = None, related_items: str = None):
        """Met à jour un élément de connaissance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if type is not None:
            updates.append("type = ?")
            params.append(type)
        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)
        if related_items is not None:
            updates.append("related_items = ?")
            params.append(related_items)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(item_id)
            query = f"UPDATE knowledge_items SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            self.backup_to_json()
    
    def delete_knowledge_item(self, item_id: int):
        """Supprime un élément de connaissance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge_items WHERE id = ?", (item_id,))
        conn.commit()
        self.backup_to_json()
    
    # ==================== FONCTIONS RAPPELS INTELLIGENTS ====================
    def add_smart_reminder(self, event_type: str, event_id: int, reminder_type: str,
                          reminder_time: str, message: str, notification_method: str = "both") -> int:
        """Ajoute un rappel intelligent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO smart_reminders (event_type, event_id, reminder_type, reminder_time, message, notification_method)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event_type, event_id, reminder_type, reminder_time, message, notification_method))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        self.backup_to_json()
        return reminder_id
    
    def get_pending_smart_reminders(self) -> List[Dict]:
        """Récupère les rappels intelligents en attente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM smart_reminders WHERE sent = 0 ORDER BY reminder_time")
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_reminder_sent(self, reminder_id: int):
        """Marque un rappel comme envoyé"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE smart_reminders SET sent = 1 WHERE id = ?", (reminder_id,))
        conn.commit()
        self.backup_to_json()
    
    # ==================== FONCTIONS HISTORIQUE NOTIFICATIONS ====================
    def add_notification_history(self, notification_type: str, recipient: str = None,
                                subject: str = None, message: str = None,
                                method: str = None, status: str = 'sent'):
        """Ajoute une entrée dans l'historique des notifications"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notification_history 
            (notification_type, recipient, subject, message, method, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (notification_type, recipient, subject, message, method, status))
        conn.commit()
        self.backup_to_json()
    
    def get_notification_history(self, limit: int = 50) -> List[Dict]:
        """Récupère l'historique des notifications"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM notification_history 
            ORDER BY sent_at DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close()
            self.conn = None


# Instance globale de la base de données
_db_instance = None

def get_db() -> Database:
    """Obtient l'instance globale de la base de données"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
