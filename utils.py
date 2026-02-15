"""
Fonctions utilitaires pour export, statistiques et notifications
"""
import pandas as pd
import io
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database import get_db
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import plotly.graph_objects as go


def export_to_csv(events: List[Dict], filename: str = None) -> bytes:
    """Exporte les événements en CSV"""
    if not events:
        return b""
    
    # Préparer les données pour le CSV
    rows = []
    for event in events:
        row = {
            'ID': event.get('id', ''),
            'Type': event.get('type', ''),
            'Nom': event.get('name', ''),
            'Date': event.get('date', ''),
            'Heure': event.get('time', ''),
            'Durée (min)': event.get('duration', 0),
            'Notes': event.get('notes', '')
        }
        
        # Ajouter les données spécifiques selon le type
        event_type = event.get('type', '')
        
        if 'Sport' in event_type and 'sport_data' in event:
            sport = event['sport_data']
            if sport:
                row['Type Séance'] = sport.get('session_type', '')
                row['Calories Brûlées'] = sport.get('calories_burned', '')
                row['Nb Exercices'] = len(sport.get('exercises', []))
                row['Nb Activités Cardio'] = len(sport.get('cardio', []))
        
        elif 'Repas' in event_type or '🍽️' in event_type:
            if 'meal_data' in event and event['meal_data']:
                meal = event['meal_data']
                row['Calories'] = meal.get('calories', '')
                row['Protéines (g)'] = meal.get('protein', '')
                row['Glucides (g)'] = meal.get('carbs', '')
                row['Lipides (g)'] = meal.get('fats', '')
        
        elif 'Sommeil' in event_type or '😴' in event_type:
            if 'sleep_data' in event and event['sleep_data']:
                sleep = event['sleep_data']
                row['Heure Coucher'] = sleep.get('bedtime', '')
                row['Heure Réveil'] = sleep.get('wake_time', '')
                row['Durée (h)'] = sleep.get('duration_hours', '')
                row['Qualité (1-5)'] = sleep.get('quality_score', '')
        
        elif 'Poids' in event_type:
            if 'weight_data' in event and event['weight_data']:
                weight = event['weight_data']
                row['Poids (kg)'] = weight.get('weight_kg', '')
                row['Masse Grasse (%)'] = weight.get('body_fat_percent', '')
                row['Masse Musculaire (%)'] = weight.get('muscle_mass_percent', '')
        
        elif 'Hydratation' in event_type or '💧' in event_type:
            if 'hydration_data' in event and event['hydration_data']:
                row['Quantité (L)'] = event['hydration_data'].get('amount_liters', '')
        
        elif 'Travail' in event_type or '💼' in event_type:
            if 'work_data' in event and event['work_data']:
                work = event['work_data']
                row['Type Tâche'] = work.get('task_type', '')
                row['Productivité (1-5)'] = work.get('productivity_score', '')
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Convertir en CSV
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    return output.getvalue().encode('utf-8-sig')


def export_to_excel(events: List[Dict], filename: str = None) -> bytes:
    """Exporte les événements en Excel"""
    if not events:
        return b""
    
    # Utiliser la même préparation que pour CSV
    rows = []
    for event in events:
        row = {
            'ID': event.get('id', ''),
            'Type': event.get('type', ''),
            'Nom': event.get('name', ''),
            'Date': event.get('date', ''),
            'Heure': event.get('time', ''),
            'Durée (min)': event.get('duration', 0),
            'Notes': event.get('notes', '')
        }
        
        event_type = event.get('type', '')
        
        if 'Sport' in event_type and 'sport_data' in event:
            sport = event['sport_data']
            if sport:
                row['Type Séance'] = sport.get('session_type', '')
                row['Calories Brûlées'] = sport.get('calories_burned', '')
                row['Nb Exercices'] = len(sport.get('exercises', []))
                row['Nb Activités Cardio'] = len(sport.get('cardio', []))
        
        elif 'Repas' in event_type or '🍽️' in event_type:
            if 'meal_data' in event and event['meal_data']:
                meal = event['meal_data']
                row['Calories'] = meal.get('calories', '')
                row['Protéines (g)'] = meal.get('protein', '')
                row['Glucides (g)'] = meal.get('carbs', '')
                row['Lipides (g)'] = meal.get('fats', '')
        
        elif 'Sommeil' in event_type or '😴' in event_type:
            if 'sleep_data' in event and event['sleep_data']:
                sleep = event['sleep_data']
                row['Heure Coucher'] = sleep.get('bedtime', '')
                row['Heure Réveil'] = sleep.get('wake_time', '')
                row['Durée (h)'] = sleep.get('duration_hours', '')
                row['Qualité (1-5)'] = sleep.get('quality_score', '')
        
        elif 'Poids' in event_type:
            if 'weight_data' in event and event['weight_data']:
                weight = event['weight_data']
                row['Poids (kg)'] = weight.get('weight_kg', '')
                row['Masse Grasse (%)'] = weight.get('body_fat_percent', '')
                row['Masse Musculaire (%)'] = weight.get('muscle_mass_percent', '')
        
        elif 'Hydratation' in event_type or '💧' in event_type:
            if 'hydration_data' in event and event['hydration_data']:
                row['Quantité (L)'] = event['hydration_data'].get('amount_liters', '')
        
        elif 'Travail' in event_type or '💼' in event_type:
            if 'work_data' in event and event['work_data']:
                work = event['work_data']
                row['Type Tâche'] = work.get('task_type', '')
                row['Productivité (1-5)'] = work.get('productivity_score', '')
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Convertir en Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Événements')
    
    output.seek(0)
    return output.read()


def export_to_pdf(events: List[Dict], period: str = "Mois", 
                 start_date: str = None, end_date: str = None) -> bytes:
    """Exporte les événements en PDF avec statistiques"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Titre
    story.append(Paragraph("Rapport d'Activités", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Période
    period_text = f"Période : {period}"
    if start_date and end_date:
        period_text += f" ({start_date} au {end_date})"
    story.append(Paragraph(period_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Statistiques générales
    story.append(Paragraph("Statistiques Générales", styles['Heading2']))
    
    total_events = len(events)
    total_duration = sum([e.get('duration', 0) for e in events])
    
    sport_events = [e for e in events if 'Sport' in e.get('type', '')]
    meal_events = [e for e in events if 'Repas' in e.get('type', '') or '🍽️' in e.get('type', '')]
    
    stats_data = [
        ['Métrique', 'Valeur'],
        ['Total d\'événements', str(total_events)],
        ['Temps total (heures)', f"{total_duration / 60:.1f}"],
        ['Séances de sport', str(len(sport_events))],
        ['Repas enregistrés', str(len(meal_events))]
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Liste des événements
    story.append(Paragraph("Événements", styles['Heading2']))
    
    if events:
        # Limiter à 50 événements pour le PDF
        events_to_show = events[:50]
        
        event_data = [['Date', 'Type', 'Nom', 'Durée (min)']]
        for event in events_to_show:
            event_data.append([
                event.get('date', ''),
                event.get('type', '')[:20],
                event.get('name', '')[:30],
                str(event.get('duration', 0))
            ])
        
        event_table = Table(event_data, colWidths=[1.5*inch, 1.5*inch, 2.5*inch, 1*inch])
        event_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(event_table)
        
        if len(events) > 50:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph(
                f"Note : Seuls les 50 premiers événements sont affichés. Total : {len(events)} événements.",
                styles['Normal']
            ))
    else:
        story.append(Paragraph("Aucun événement à afficher.", styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        styles['Normal']
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def calculate_sport_statistics(events: List[Dict]) -> Dict:
    """Calcule les statistiques sportives"""
    sport_events = [e for e in events if 'Sport' in e.get('type', '')]
    
    if not sport_events:
        return {
            'total_sessions': 0,
            'total_duration': 0,
            'total_calories': 0,
            'avg_duration': 0,
            'sessions_by_type': {}
        }
    
    total_duration = sum([e.get('duration', 0) for e in sport_events])
    total_calories = 0
    sessions_by_type = {}
    
    for event in sport_events:
        if 'sport_data' in event and event['sport_data']:
            sport = event['sport_data']
            session_type = sport.get('session_type', 'Non spécifié')
            sessions_by_type[session_type] = sessions_by_type.get(session_type, 0) + 1
            total_calories += sport.get('calories_burned', 0) or 0
    
    return {
        'total_sessions': len(sport_events),
        'total_duration': total_duration,
        'total_calories': total_calories,
        'avg_duration': total_duration / len(sport_events) if sport_events else 0,
        'sessions_by_type': sessions_by_type
    }


def calculate_nutrition_statistics(events: List[Dict], date: str = None) -> Dict:
    """Calcule les statistiques nutritionnelles"""
    meal_events = [e for e in events if 'Repas' in e.get('type', '') or '🍽️' in e.get('type', '')]
    
    if date:
        meal_events = [e for e in meal_events if e.get('date') == date]
    
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fats = 0
    
    for event in meal_events:
        if 'meal_data' in event and event['meal_data']:
            meal = event['meal_data']
            total_calories += meal.get('calories', 0) or 0
            total_protein += meal.get('protein', 0) or 0
            total_carbs += meal.get('carbs', 0) or 0
            total_fats += meal.get('fats', 0) or 0
    
    return {
        'total_meals': len(meal_events),
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_carbs': total_carbs,
        'total_fats': total_fats
    }


def calculate_sleep_statistics(events: List[Dict]) -> Dict:
    """Calcule les statistiques de sommeil"""
    sleep_events = [e for e in events if 'Sommeil' in e.get('type', '') or '😴' in e.get('type', '')]
    
    if not sleep_events:
        return {
            'total_records': 0,
            'avg_duration': 0,
            'avg_quality': 0
        }
    
    total_duration = 0
    total_quality = 0
    quality_count = 0
    
    for event in sleep_events:
        if 'sleep_data' in event and event['sleep_data']:
            sleep = event['sleep_data']
            duration = sleep.get('duration_hours', 0) or 0
            total_duration += duration
            quality = sleep.get('quality_score', 0) or 0
            if quality > 0:
                total_quality += quality
                quality_count += 1
    
    return {
        'total_records': len(sleep_events),
        'avg_duration': total_duration / len(sleep_events) if sleep_events else 0,
        'avg_quality': total_quality / quality_count if quality_count > 0 else 0
    }


def get_today_sport_count() -> int:
    """Retourne le nombre de séances de sport aujourd'hui"""
    db = get_db()
    today = datetime.now().date().isoformat()
    events = db.get_all_events({'date_from': today, 'date_to': today})
    sport_events = [e for e in events if 'Sport' in e.get('type', '')]
    return len(sport_events)


def get_today_hydration() -> float:
    """Retourne la quantité totale d'eau bue aujourd'hui"""
    db = get_db()
    today = datetime.now().date().isoformat()
    events = db.get_all_events({'date_from': today, 'date_to': today})
    hydration_events = [e for e in events if 'Hydratation' in e.get('type', '') or '💧' in e.get('type', '')]
    
    total = 0.0
    for event in hydration_events:
        if 'hydration_data' in event and event['hydration_data']:
            total += event['hydration_data'].get('amount_liters', 0) or 0
    
    return total


def get_yesterday_sleep() -> Optional[Dict]:
    """Retourne les données de sommeil d'hier"""
    db = get_db()
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
    events = db.get_all_events({'date_from': yesterday, 'date_to': yesterday})
    sleep_events = [e for e in events if 'Sommeil' in e.get('type', '') or '😴' in e.get('type', '')]
    
    if sleep_events and 'sleep_data' in sleep_events[0]:
        return sleep_events[0]['sleep_data']
    
    return None


def get_latest_weight() -> Optional[float]:
    """Retourne le dernier poids enregistré"""
    db = get_db()
    events = db.get_all_events()
    weight_events = [e for e in events if 'Poids' in e.get('type', '')]
    
    if weight_events:
        # Trier par date décroissante
        weight_events.sort(key=lambda x: x.get('date', ''), reverse=True)
        latest = weight_events[0]
        if 'weight_data' in latest and latest['weight_data']:
            return latest['weight_data'].get('weight_kg')
    
    return None


def get_active_reminders() -> List[Dict]:
    """Retourne les rappels actifs pour aujourd'hui"""
    db = get_db()
    reminders = db.get_all_reminders(enabled_only=True)
    
    # Filtrer selon la fréquence et l'heure
    active_reminders = []
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    for reminder in reminders:
        frequency = reminder.get('frequency', '')
        reminder_time = reminder.get('time', '')
        
        if frequency == 'Quotidien':
            # Vérifier si l'heure est passée aujourd'hui
            if reminder_time <= current_time:
                active_reminders.append(reminder)
        elif frequency == 'Hebdomadaire':
            # Pour simplifier, on affiche tous les rappels hebdomadaires
            active_reminders.append(reminder)
        else:
            # Personnalisé - à implémenter selon les besoins
            active_reminders.append(reminder)
    
    return active_reminders
