"""
Module d'analyses avancées pour le tracker de vie
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database import get_db


def analyze_study_time(events: List[Dict], days: int = 30) -> Dict:
    """Analyse le temps de travail/étude"""
    db = get_db()
    
    # Filtrer les événements de travail/étude
    study_events = [e for e in events if 'Travail' in e.get('type', '') or 'Étude' in e.get('type', '')]
    
    if not study_events:
        return {
            'total_hours': 0,
            'avg_daily_hours': 0,
            'daily_breakdown': [],
            'weekly_breakdown': [],
            'trend': 'stable'
        }
    
    # Calculer le temps total
    total_minutes = sum([e.get('duration', 0) for e in study_events])
    total_hours = total_minutes / 60
    
    # Breakdown par jour
    study_df = pd.DataFrame(study_events)
    study_df['date'] = pd.to_datetime(study_df['date'])
    study_df['date_only'] = study_df['date'].dt.date
    
    daily_study = study_df.groupby('date_only')['duration'].sum().reset_index()
    daily_study['hours'] = daily_study['duration'] / 60
    daily_study = daily_study.sort_values('date_only')
    
    # Breakdown par semaine
    study_df['week'] = study_df['date'].dt.isocalendar().week
    study_df['year'] = study_df['date'].dt.year
    weekly_study = study_df.groupby(['year', 'week'])['duration'].sum().reset_index()
    weekly_study['hours'] = weekly_study['duration'] / 60
    
    # Tendance
    if len(daily_study) > 1:
        recent_avg = daily_study.tail(7)['hours'].mean() if len(daily_study) >= 7 else daily_study['hours'].mean()
        older_avg = daily_study.head(max(1, len(daily_study) - 7))['hours'].mean() if len(daily_study) > 7 else recent_avg
        if recent_avg > older_avg * 1.1:
            trend = 'increasing'
        elif recent_avg < older_avg * 0.9:
            trend = 'decreasing'
        else:
            trend = 'stable'
    else:
        trend = 'stable'
    
    avg_daily_hours = total_hours / days if days > 0 else 0
    
    return {
        'total_hours': total_hours,
        'avg_daily_hours': avg_daily_hours,
        'daily_breakdown': daily_study.to_dict('records'),
        'weekly_breakdown': weekly_study.to_dict('records'),
        'trend': trend
    }


def analyze_productivity(events: List[Dict], days: int = 30) -> Dict:
    """Analyse la productivité"""
    db = get_db()
    
    # Filtrer les événements de travail avec score de productivité
    work_events = [e for e in events if 'Travail' in e.get('type', '')]
    
    productivity_scores = []
    productivity_by_date = {}
    
    for event in work_events:
        if 'work_data' in event and event['work_data']:
            score = event['work_data'].get('productivity_score')
            if score:
                productivity_scores.append(score)
                event_date = event.get('date', '')
                if event_date not in productivity_by_date:
                    productivity_by_date[event_date] = []
                productivity_by_date[event_date].append(score)
    
    if not productivity_scores:
        return {
            'avg_score': 0,
            'scores_by_date': [],
            'correlation_sleep': None,
            'correlation_sport': None,
            'trend': 'stable'
        }
    
    avg_score = sum(productivity_scores) / len(productivity_scores)
    
    # Scores par date
    scores_by_date = []
    for date, scores in productivity_by_date.items():
        scores_by_date.append({
            'date': date,
            'avg_score': sum(scores) / len(scores),
            'count': len(scores)
        })
    
    scores_df = pd.DataFrame(scores_by_date)
    scores_df = scores_df.sort_values('date')
    
    # Corrélation avec sommeil
    sleep_events = [e for e in events if 'Sommeil' in e.get('type', '')]
    correlation_sleep = None
    if sleep_events and productivity_scores:
        # Simplifié : moyenne du sommeil vs productivité
        sleep_hours = []
        for event in sleep_events:
            if 'sleep_data' in event and event['sleep_data']:
                hours = event['sleep_data'].get('duration_hours', 0)
                if hours:
                    sleep_hours.append(hours)
        
        if sleep_hours and len(sleep_hours) == len(productivity_scores):
            correlation_sleep = pd.Series(sleep_hours).corr(pd.Series(productivity_scores))
    
    # Corrélation avec sport
    sport_events = [e for e in events if 'Sport' in e.get('type', '')]
    correlation_sport = None
    if sport_events:
        # Nombre de séances de sport par jour vs productivité
        pass  # À implémenter si nécessaire
    
    # Tendance
    if len(scores_df) > 1:
        recent_avg = scores_df.tail(7)['avg_score'].mean() if len(scores_df) >= 7 else scores_df['avg_score'].mean()
        older_avg = scores_df.head(max(1, len(scores_df) - 7))['avg_score'].mean() if len(scores_df) > 7 else recent_avg
        if recent_avg > older_avg * 1.1:
            trend = 'increasing'
        elif recent_avg < older_avg * 0.9:
            trend = 'decreasing'
        else:
            trend = 'stable'
    else:
        trend = 'stable'
    
    return {
        'avg_score': avg_score,
        'scores_by_date': scores_by_date,
        'correlation_sleep': correlation_sleep,
        'correlation_sport': correlation_sport,
        'trend': trend
    }


def analyze_habits(events: List[Dict], habit_type: str = 'sport', days: int = 30) -> Dict:
    """Analyse des habitudes (sport, sommeil, etc.)"""
    db = get_db()
    
    # Filtrer selon le type d'habitude
    if habit_type == 'sport':
        habit_events = [e for e in events if 'Sport' in e.get('type', '')]
    elif habit_type == 'sleep':
        habit_events = [e for e in events if 'Sommeil' in e.get('type', '')]
    else:
        habit_events = []
    
    if not habit_events:
        return {
            'consistency_score': 0,
            'frequency': 0,
            'patterns': [],
            'heatmap_data': {}
        }
    
    # Créer un DataFrame
    habit_df = pd.DataFrame(habit_events)
    habit_df['date'] = pd.to_datetime(habit_df['date'])
    habit_df['date_only'] = habit_df['date'].dt.date
    habit_df['day_of_week'] = habit_df['date'].dt.dayofweek
    
    # Fréquence
    unique_days = habit_df['date_only'].nunique()
    frequency = unique_days / days if days > 0 else 0
    
    # Patterns par jour de la semaine
    patterns = habit_df.groupby('day_of_week').size().to_dict()
    
    # Score de consistance (écart-type de la fréquence)
    daily_counts = habit_df.groupby('date_only').size()
    if len(daily_counts) > 1:
        consistency_score = 1 - (daily_counts.std() / daily_counts.mean()) if daily_counts.mean() > 0 else 0
        consistency_score = max(0, min(1, consistency_score))  # Entre 0 et 1
    else:
        consistency_score = 1 if len(daily_counts) == 1 else 0
    
    # Données pour heatmap
    heatmap_data = {}
    for date, count in daily_counts.items():
        heatmap_data[date.isoformat()] = count
    
    return {
        'consistency_score': consistency_score,
        'frequency': frequency,
        'patterns': patterns,
        'heatmap_data': heatmap_data
    }


def analyze_goals_progress(objectives: List[Dict], events: List[Dict]) -> Dict:
    """Analyse la progression des objectifs"""
    db = get_db()
    
    if not objectives:
        return {
            'total_objectives': 0,
            'completed': 0,
            'in_progress': 0,
            'progress_details': []
        }
    
    completed = 0
    in_progress = 0
    progress_details = []
    
    for obj in objectives:
        current = obj.get('current_value', 0) or 0
        target = obj.get('target_value', 0) or 1
        progress = min(current / target, 1.0) if target > 0 else 0
        
        status = obj.get('status', 'active')
        if status == 'completed':
            completed += 1
        elif status == 'active':
            in_progress += 1
        
        progress_details.append({
            'name': obj.get('name', ''),
            'current': current,
            'target': target,
            'progress': progress,
            'status': status
        })
    
    return {
        'total_objectives': len(objectives),
        'completed': completed,
        'in_progress': in_progress,
        'progress_details': progress_details
    }


def generate_heatmap(events: List[Dict], event_type: str = 'sport', days: int = 30) -> go.Figure:
    """Génère une heatmap (calendrier de présence)"""
    # Filtrer les événements
    filtered_events = [e for e in events if event_type in e.get('type', '')]
    
    if not filtered_events:
        # Retourner une heatmap vide
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée disponible", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    # Créer un DataFrame
    df = pd.DataFrame(filtered_events)
    df['date'] = pd.to_datetime(df['date'])
    df['date_only'] = df['date'].dt.date
    
    # Compter les événements par jour
    daily_counts = df.groupby('date_only').size().reset_index(name='count')
    
    # Créer une plage de dates
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Créer une matrice pour la heatmap
    heatmap_data = []
    for date in date_range:
        date_str = date.date().isoformat()
        count = daily_counts[daily_counts['date_only'] == date.date()]['count'].values
        heatmap_data.append({
            'date': date_str,
            'count': count[0] if len(count) > 0 else 0
        })
    
    heatmap_df = pd.DataFrame(heatmap_data)
    
    # Créer la heatmap
    fig = go.Figure(data=go.Scatter(
        x=heatmap_df['date'],
        y=heatmap_df['count'],
        mode='markers',
        marker=dict(
            size=10,
            color=heatmap_df['count'],
            colorscale='Viridis',
            showscale=True
        )
    ))
    
    fig.update_layout(
        title=f"Heatmap - {event_type} ({days} derniers jours)",
        xaxis_title="Date",
        yaxis_title="Nombre d'événements"
    )
    
    return fig
