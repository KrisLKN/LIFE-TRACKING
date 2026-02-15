"""
Script pour vérifier et envoyer les rappels intelligents
À exécuter périodiquement (cron job ou scheduler)
"""
import sys
from datetime import datetime, timedelta
from database import get_db
from notifications import send_exam_reminder, send_tupperware_reminder, send_event_reminder

def check_and_send_reminders():
    """Vérifie et envoie les rappels en attente"""
    db = get_db()
    
    # Vérifier les examens
    exams = db.get_all_exams(upcoming_only=True)
    for exam in exams:
        exam_date = datetime.fromisoformat(exam.get('exam_date', datetime.now().isoformat()))
        if exam.get('exam_time'):
            exam_time = datetime.strptime(exam.get('exam_time'), "%H:%M").time()
            exam_datetime = datetime.combine(exam_date.date(), exam_time)
        else:
            exam_datetime = exam_date
        
        reminder_days = exam.get('reminder_days_before', 1)
        days_until = (exam_datetime.date() - datetime.now().date()).days
        
        if days_until == reminder_days and not exam.get('notification_sent', 0):
            result = send_exam_reminder(
                exam_name=exam.get('name', ''),
                exam_date=exam_datetime,
                days_before=reminder_days
            )
            if result.get('email') or result.get('telegram'):
                # Marquer comme envoyé (à implémenter dans database.py si nécessaire)
                print(f"Rappel envoyé pour l'examen: {exam.get('name', '')}")
    
    # Vérifier les rappels Tupperware pour demain
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_weekday = tomorrow.weekday()
    courses_tomorrow = db.get_courses_by_day(tomorrow_weekday)
    
    for course in courses_tomorrow:
        if course.get('tupperware_reminder', 0):
            result = send_tupperware_reminder(tomorrow)
            if result.get('email') or result.get('telegram'):
                print(f"Rappel Tupperware envoyé pour: {course.get('name', '')}")
    
    # Vérifier les rappels intelligents en attente
    smart_reminders = db.get_pending_smart_reminders()
    for reminder in smart_reminders:
        reminder_time = datetime.fromisoformat(reminder.get('reminder_time', datetime.now().isoformat()))
        
        # Si le rappel est dû (dans les prochaines heures)
        if reminder_time <= datetime.now() + timedelta(hours=1):
            event_type = reminder.get('event_type', '')
            event_id = reminder.get('event_id', 0)
            
            if event_type == 'exam':
                exams = [e for e in db.get_all_exams() if e.get('id') == event_id]
                if exams:
                    exam = exams[0]
                    exam_date = datetime.fromisoformat(exam.get('exam_date', datetime.now().isoformat()))
                    result = send_exam_reminder(
                        exam_name=exam.get('name', ''),
                        exam_date=exam_date,
                        days_before=1
                    )
            else:
                # Rappel générique
                result = send_event_reminder(
                    event_name=reminder.get('message', 'Événement'),
                    event_date=reminder_time,
                    reminder_type=reminder.get('reminder_type', 'général')
                )
            
            if result.get('email') or result.get('telegram'):
                db.mark_reminder_sent(reminder.get('id'))
                print(f"Rappel intelligent envoyé: {reminder.get('message', '')}")

if __name__ == "__main__":
    check_and_send_reminders()
