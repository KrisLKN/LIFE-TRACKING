"""
Module de notifications par Email et Telegram
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

try:
    import requests
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

logger = logging.getLogger(__name__)


class NotificationService:
    """Service de notifications par Email et Telegram"""
    
    def __init__(self):
        self.email_config = self._load_email_config()
        self.telegram_config = self._load_telegram_config()
    
    def _load_email_config(self) -> Dict:
        """Charge la configuration email depuis les variables d'environnement ou fichier"""
        return {
            'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'sender_email': os.getenv('EMAIL_SENDER', ''),
            'sender_password': os.getenv('EMAIL_PASSWORD', ''),
            'enabled': os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        }
    
    def _load_telegram_config(self) -> Dict:
        """Charge la configuration Telegram depuis les variables d'environnement"""
        return {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
            'enabled': os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
        }
    
    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Envoie un email"""
        if not self.email_config['enabled'] or not self.email_config['sender_email']:
            logger.warning("Email non configuré ou désactivé")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['sender_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Ajouter le texte et HTML
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Connexion et envoi
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email envoyé à {to_email}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'email : {e}")
            return False
    
    def send_telegram(self, message: str) -> bool:
        """Envoie un message Telegram"""
        if not self.telegram_config['enabled'] or not self.telegram_config['bot_token']:
            logger.warning("Telegram non configuré ou désactivé")
            return False
        
        if not TELEGRAM_AVAILABLE:
            logger.warning("Bibliothèque requests non disponible pour Telegram")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            payload = {
                'chat_id': self.telegram_config['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            logger.info("Message Telegram envoyé")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi Telegram : {e}")
            return False
    
    def send_notification(self, message: str, subject: Optional[str] = None, 
                         use_email: bool = True, use_telegram: bool = True) -> Dict[str, bool]:
        """Envoie une notification via email et/ou Telegram"""
        results = {'email': False, 'telegram': False}
        
        if use_email and self.email_config['enabled']:
            email_subject = subject or "Notification - Planificateur de Vie"
            html_message = f"<p>{message.replace(chr(10), '<br>')}</p>"
            results['email'] = self.send_email(
                to_email=self.email_config['sender_email'],  # Par défaut, s'envoyer à soi-même
                subject=email_subject,
                body=message,
                html_body=html_message
            )
        
        if use_telegram and self.telegram_config['enabled']:
            telegram_message = f"<b>{subject or 'Notification'}</b>\n\n{message}"
            results['telegram'] = self.send_telegram(telegram_message)
        
        return results


def send_exam_reminder(exam_name: str, exam_date: datetime, days_before: int = 1) -> Dict[str, bool]:
    """Envoie un rappel pour un examen"""
    service = NotificationService()
    
    days_remaining = (exam_date.date() - datetime.now().date()).days
    
    if days_remaining == days_before:
        message = f"📚 Rappel Examen : {exam_name}\n"
        message += f"Date : {exam_date.strftime('%d/%m/%Y à %H:%M')}\n"
        message += f"Dans {days_remaining} jour(s) !\n"
        message += "N'oublie pas de réviser ! 💪"
        
        return service.send_notification(
            message=message,
            subject=f"Rappel Examen : {exam_name}",
            use_email=True,
            use_telegram=True
        )
    
    return {'email': False, 'telegram': False}


def send_tupperware_reminder(school_date: datetime) -> Dict[str, bool]:
    """Envoie un rappel pour préparer le Tupperware la veille"""
    service = NotificationService()
    
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    school_date_only = school_date.date() if isinstance(school_date, datetime) else school_date
    
    # Si c'est la veille de l'école
    if school_date_only == tomorrow:
        message = "🍱 Rappel Tupperware !\n"
        message += f"Tu as école demain ({school_date_only.strftime('%d/%m/%Y')})\n"
        message += "N'oublie pas de préparer ton repas pour demain ! 🥗"
        
        return service.send_notification(
            message=message,
            subject="Rappel : Préparer ton Tupperware",
            use_email=True,
            use_telegram=True
        )
    
    return {'email': False, 'telegram': False}


def send_event_reminder(event_name: str, event_date: datetime, 
                       reminder_type: str = "général") -> Dict[str, bool]:
    """Envoie un rappel pour un événement planifié"""
    service = NotificationService()
    
    # Vérifier si l'événement est dans les prochaines heures
    time_diff = event_date - datetime.now()
    hours_until = time_diff.total_seconds() / 3600
    
    if 0 <= hours_until <= 24:  # Dans les 24 prochaines heures
        hours = int(hours_until)
        message = f"⏰ Rappel : {event_name}\n"
        message += f"Date : {event_date.strftime('%d/%m/%Y à %H:%M')}\n"
        
        if hours == 0:
            message += "C'est maintenant ! 🚀"
        elif hours == 1:
            message += "Dans 1 heure !"
        else:
            message += f"Dans {hours} heures"
        
        return service.send_notification(
            message=message,
            subject=f"Rappel : {event_name}",
            use_email=True,
            use_telegram=True
        )
    
    return {'email': False, 'telegram': False}


# Instance globale
_notification_service = None

def get_notification_service() -> NotificationService:
    """Obtient l'instance globale du service de notifications"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


def check_and_send_reminders():
    """Vérifie et envoie tous les rappels automatiques (examens, devoirs, cours)"""
    from database import get_db
    
    db = get_db()
    service = get_notification_service()
    results = {'exams': 0, 'assignments': 0, 'courses': 0}
    
    # Vérifier les rappels d'examens
    exams = db.get_upcoming_exams(days=30)
    for exam in exams:
        exam_date = datetime.fromisoformat(exam.get('exam_date', datetime.now().isoformat()))
        days_before = exam.get('reminder_days_before', 1)
        reminder_date = exam_date.date() - timedelta(days=days_before)
        today = datetime.now().date()
        
        # Vérifier si le rappel doit être envoyé aujourd'hui
        if reminder_date == today and exam.get('notification_sent', 0) == 0:
            result = send_exam_reminder(
                exam_name=exam.get('name', ''),
                exam_date=exam_date,
                days_before=days_before
            )
            if result.get('email') or result.get('telegram'):
                # Marquer comme envoyé
                db.update_exam(exam.get('id'), notification_sent=1)
                results['exams'] += 1
                # Enregistrer dans l'historique
                db.add_notification_history(
                    notification_type="exam_reminder",
                    subject=f"Rappel Examen : {exam.get('name', '')}",
                    message=f"Examen {exam.get('name', '')} dans {days_before} jour(s)",
                    method="both" if (result.get('email') and result.get('telegram')) else ("email" if result.get('email') else "telegram"),
                    status="sent"
                )
    
    # Vérifier les rappels de devoirs
    assignments = db.get_upcoming_assignments(days=7)
    for assign in assignments:
        due_date = datetime.fromisoformat(assign.get('due_date', datetime.now().isoformat()))
        days_until = (due_date.date() - datetime.now().date()).days
        
        # Envoyer un rappel 1 jour avant et le jour même
        if days_until <= 1 and assign.get('status') != 'completed':
            message = f"📝 Rappel Devoir : {assign.get('title', '')}\n"
            message += f"Date limite : {due_date.strftime('%d/%m/%Y à %H:%M')}\n"
            if days_until == 0:
                message += "⚠️ C'est aujourd'hui !"
            else:
                message += f"Dans {days_until} jour(s) !"
            
            result = service.send_notification(
                message=message,
                subject=f"Rappel Devoir : {assign.get('title', '')}",
                use_email=True,
                use_telegram=True
            )
            if result.get('email') or result.get('telegram'):
                results['assignments'] += 1
                db.add_notification_history(
                    notification_type="assignment_reminder",
                    subject=f"Rappel Devoir : {assign.get('title', '')}",
                    message=message,
                    method="both" if (result.get('email') and result.get('telegram')) else ("email" if result.get('email') else "telegram"),
                    status="sent"
                )
    
    # Vérifier les rappels Tupperware (la veille des jours de cours)
    tomorrow = datetime.now().date() + timedelta(days=1)
    tomorrow_weekday = tomorrow.weekday()
    courses_tomorrow = db.get_courses_by_day(tomorrow_weekday)
    
    for course in courses_tomorrow:
        if course.get('tupperware_reminder', 0) == 1:
            result = send_tupperware_reminder(tomorrow)
            if result.get('email') or result.get('telegram'):
                results['courses'] += 1
                db.add_notification_history(
                    notification_type="tupperware_reminder",
                    subject="Rappel : Préparer ton Tupperware",
                    message=f"Tu as école demain ({tomorrow.strftime('%d/%m/%Y')})",
                    method="both" if (result.get('email') and result.get('telegram')) else ("email" if result.get('email') else "telegram"),
                    status="sent"
                )
    
    return results