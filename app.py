"""
Application Streamlit - Planificateur d'Événements Complet
Tracker de vie avec suivi détaillé des activités
"""
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging

logger = logging.getLogger(__name__)

from database import get_db
from config import (
    EVENT_TYPES, SPORT_SESSION_TYPES, CARDIO_TYPES, OBJECTIVE_TYPES,
    OBJECTIVE_FREQUENCIES, REMINDER_TYPES, REMINDER_FREQUENCIES,
    DEFAULT_SPORT_SESSIONS_PER_DAY, WEEKDAYS, SECOND_BRAIN_CATEGORIES,
    KNOWLEDGE_TYPES, ASSIGNMENT_STATUS, PRIORITIES
)
from utils import (
    export_to_csv, export_to_excel, export_to_pdf,
    calculate_sport_statistics, calculate_nutrition_statistics,
    calculate_sleep_statistics, get_today_sport_count, get_today_hydration,
    get_yesterday_sleep, get_latest_weight, get_active_reminders
)
from notifications import (
    get_notification_service, send_exam_reminder, send_tupperware_reminder,
    send_event_reminder, check_and_send_reminders
)
from theme import (
    init_theme, toggle_dark_mode, is_dark_mode, get_theme_css,
    inject_font_awesome, inject_custom_css, emoji_to_icon, get_icon_html, render_icon_text
)

# Configuration de la page
st.set_page_config(
    page_title="Planificateur d'Événements - Tracker de Vie",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injection de Font Awesome et CSS personnalisé dans le head
st.markdown("""
    <head>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" 
              integrity="sha512-iecdLmaskl7CVkqkXNQ/ZH/XLlvWZOJyj7Yy7tcenmpD1ypASozpmT/E0iPtmFIB46ZmdtAc9eNBvH0H/ZpiBw==" 
              crossorigin="anonymous" 
              referrerpolicy="no-referrer" />
        <style>
            .fa-icon, .fa-icon-small, .fa-icon-large {
                display: inline-block;
                margin-right: 0.5rem;
            }
            .fa-icon-small { font-size: 0.9em; }
            .fa-icon { font-size: 1.2em; }
            .fa-icon-large { font-size: 1.5em; }
        </style>
    </head>
""", unsafe_allow_html=True)
st.markdown(inject_custom_css(), unsafe_allow_html=True)

# Initialisation du thème
init_theme()

# Application du thème
st.markdown(get_theme_css(), unsafe_allow_html=True)

# Initialisation de la base de données
@st.cache_resource
def init_db():
    return get_db()

db = init_db()

# Initialisation de l'état de session
if 'exercises' not in st.session_state:
    st.session_state.exercises = []
if 'cardio_activities' not in st.session_state:
    st.session_state.cardio_activities = []

# Vérifier et envoyer les rappels automatiques
@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def check_reminders():
    try:
        return check_and_send_reminders()
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des rappels: {e}")
        return {'exams': 0, 'assignments': 0, 'courses': 0}

# Vérifier les rappels (une fois par session)
if 'reminders_checked' not in st.session_state:
    check_reminders()
    st.session_state.reminders_checked = True

# Titre principal avec icône
st.markdown(f"""
    <h1 style="display: flex; align-items: center; gap: 0.5rem;">
        {get_icon_html('fa-calendar-days', 'large')}
        Planificateur d'Événements - Tracker de Vie
    </h1>
""", unsafe_allow_html=True)
st.markdown("---")

# Sidebar pour navigation
st.sidebar.markdown(f"""
    <h2 style="display: flex; align-items: center; gap: 0.5rem;">
        {get_icon_html('fa-bullseye', 'normal')}
        Navigation
    </h2>
""", unsafe_allow_html=True)

# Toggle mode nuit
st.sidebar.markdown("---")
dark_mode_emoji = '🌙' if not is_dark_mode() else '☀️'
dark_mode_text = "Mode Nuit" if not is_dark_mode() else "Mode Jour"
if st.sidebar.button(f"{dark_mode_emoji} {dark_mode_text}", use_container_width=True):
    toggle_dark_mode()
    st.rerun()

st.sidebar.markdown("---")

# Navigation avec icônes (utiliser emojis pour les radio buttons car Streamlit ne supporte pas HTML dans les labels)
page_options = [
    ("🏠", "fa-home", "Dashboard"),
    ("➕", "fa-plus", "Ajouter Événement"),
    ("📊", "fa-chart-line", "Tableau de Bord"),
    ("📈", "fa-chart-bar", "Statistiques"),
    ("🎯", "fa-bullseye", "Objectifs"),
    ("🏫", "fa-school", "École"),
    ("🧠", "fa-brain", "Second Cerveau"),
    ("🗓️", "fa-calendar", "Calendrier"),
    ("📤", "fa-download", "Export"),
    ("🔔", "fa-bell", "Rappels"),
    ("⚙️", "fa-gear", "Configuration")
]

# Utiliser emojis pour les radio buttons (Streamlit ne supporte pas HTML dans les labels)
page_labels = [f"{emoji} {label}" for emoji, _, label in page_options]
page = st.sidebar.radio("Choisir une page", page_labels, index=0)

# Extraire le nom de la page pour les comparaisons
page_index = page_labels.index(page) if page in page_labels else 0
current_page = page_options[page_index][2]  # Le label (nom de la page)

# Fonction helper pour subheader avec icône
def subheader_with_icon(icon_name, text):
    """Affiche un subheader avec une icône Font Awesome"""
    st.markdown(f"""
        <h3 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html(icon_name, 'normal')}
            {text}
        </h3>
    """, unsafe_allow_html=True)

# ==================== PAGE DASHBOARD ====================
if current_page == "Dashboard":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-home', 'normal')}
            Dashboard
        </h2>
    """, unsafe_allow_html=True)
    
    # Récupérer les données
    today = datetime.now().date().isoformat()
    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).date().isoformat()
    
    all_events = db.get_all_events()
    today_events = db.get_all_events({'date_from': today, 'date_to': today})
    week_events = db.get_all_events({'date_from': week_start})
    
    # Métriques clés
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        sport_count = get_today_sport_count()
        progress = min(sport_count / DEFAULT_SPORT_SESSIONS_PER_DAY, 1.0)
        st.markdown(f'<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">{get_icon_html("fa-dumbbell", "normal")} Sport Aujourd\'hui</div>', unsafe_allow_html=True)
        st.metric("", f"{sport_count}/{DEFAULT_SPORT_SESSIONS_PER_DAY}")
        st.progress(progress)
    
    with col2:
        nutrition = calculate_nutrition_statistics(today_events, today)
        st.markdown(f'<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">{get_icon_html("fa-utensils", "normal")} Calories Aujourd\'hui</div>', unsafe_allow_html=True)
        st.metric("", f"{nutrition['total_calories']} kcal")
    
    with col3:
        sleep_data = get_yesterday_sleep()
        st.markdown(f'<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">{get_icon_html("fa-moon", "normal")} Sommeil Hier</div>', unsafe_allow_html=True)
        if sleep_data:
            hours = sleep_data.get('duration_hours', 0) or 0
            st.metric("", f"{hours:.1f}h")
        else:
            st.metric("", "N/A")
    
    with col4:
        hydration = get_today_hydration()
        st.markdown(f'<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">{get_icon_html("fa-droplet", "normal")} Hydratation Aujourd\'hui</div>', unsafe_allow_html=True)
        st.metric("", f"{hydration:.2f}L")
    
    with col5:
        weight = get_latest_weight()
        st.markdown(f'<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">{get_icon_html("fa-weight-scale", "normal")} Poids Actuel</div>', unsafe_allow_html=True)
        if weight:
            st.metric("", f"{weight:.1f} kg")
        else:
            st.metric("", "N/A")
    
    st.markdown("---")
    
    # Rappels actifs
    reminders = get_active_reminders()
    if reminders:
        subheader_with_icon('fa-bell', 'Rappels')
        for reminder in reminders[:5]:  # Limiter à 5
            st.info(f"**{reminder.get('type', '')}** : {reminder.get('message', '')}")
    
    st.markdown("---")
    
    # Graphiques rapides
    col1, col2 = st.columns(2)
    
    with col1:
        subheader_with_icon('fa-chart-line', 'Sport - 7 Derniers Jours')
        sport_events = [e for e in week_events if 'Sport' in e.get('type', '')]
        if sport_events:
            sport_df = pd.DataFrame(sport_events)
            sport_df['date'] = pd.to_datetime(sport_df['date'])
            daily_sport = sport_df.groupby('date').size().reset_index(name='séances')
            daily_sport = daily_sport.sort_values('date')
            
            fig = px.line(
                daily_sport,
                x='date',
                y='séances',
                title="Séances par Jour",
                markers=True
            )
            fig.add_hline(
                y=DEFAULT_SPORT_SESSIONS_PER_DAY,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Objectif: {DEFAULT_SPORT_SESSIONS_PER_DAY}/jour"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune séance de sport cette semaine")
    
    with col2:
        subheader_with_icon('fa-chart-bar', 'Évolution du Poids')
        weight_events = [e for e in all_events if 'Poids' in e.get('type', '')]
        if weight_events:
            weights = []
            dates = []
            for event in sorted(weight_events, key=lambda x: x.get('date', '')):
                if 'weight_data' in event and event['weight_data']:
                    w = event['weight_data'].get('weight_kg')
                    if w:
                        weights.append(w)
                        dates.append(event.get('date', ''))
            
            if weights:
                fig = px.line(
                    x=dates,
                    y=weights,
                    title="Poids (kg)",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune donnée de poids disponible")
        else:
            st.info("Aucun enregistrement de poids")
    
    # Objectifs en cours
    subheader_with_icon('fa-bullseye', 'Objectifs en Cours')
    objectives = db.get_all_objectives(status='active')
    if objectives:
        obj_cols = st.columns(min(len(objectives), 3))
        for idx, obj in enumerate(objectives[:3]):
            with obj_cols[idx % 3]:
                progress = min((obj.get('current_value', 0) or 0) / (obj.get('target_value', 1) or 1), 1.0)
                st.metric(obj.get('name', ''), f"{obj.get('current_value', 0):.1f}/{obj.get('target_value', 0):.1f}")
                st.progress(progress)
    else:
        st.info("Aucun objectif actif")
    
    # Section École
    subheader_with_icon('fa-book', 'À Venir - École')
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**📚 Prochains Examens**")
        upcoming_exams = db.get_upcoming_exams(days=30)[:5]
        if upcoming_exams:
            for exam in upcoming_exams:
                exam_date = datetime.fromisoformat(exam.get('exam_date', datetime.now().isoformat())).date()
                days_until = (exam_date - datetime.now().date()).days
                st.write(f"• {exam.get('name', '')} - {days_until}j")
        else:
            st.info("Aucun examen à venir")
    
    with col2:
        st.write("**📝 Devoirs Urgents**")
        urgent_assignments = db.get_upcoming_assignments(days=7)
        if urgent_assignments:
            for assign in urgent_assignments[:5]:
                due_date = datetime.fromisoformat(assign.get('due_date', datetime.now().isoformat())).date()
                days_until = (due_date - datetime.now().date()).days
                priority = PRIORITIES.get(assign.get('priority', 3), '🟡')
                st.write(f"{priority} {assign.get('title', '')} - {days_until}j")
        else:
            st.info("Aucun devoir urgent")
    
    with col3:
        st.write("**📖 Cours de la Semaine**")
        courses_by_day = db.get_courses_for_week()
        today_weekday = datetime.now().weekday()
        week_courses = []
        for day in range(7):
            if day in courses_by_day:
                for course in courses_by_day[day]:
                    week_courses.append((day, course))
        
        if week_courses:
            for day, course in week_courses[:5]:
                day_name = WEEKDAYS[day]
                st.write(f"• {day_name}: {course.get('name', '')}")
        else:
            st.info("Aucun cours cette semaine")
    
    st.markdown("---")
    
    # Derniers événements
    subheader_with_icon('fa-clipboard-list', 'Derniers Événements')
    recent_events = all_events[:10]
    if recent_events:
        for event in recent_events:
            with st.expander(f"{event.get('type', '')} - {event.get('name', '')} | {event.get('date', '')}"):
                st.write(f"**Heure:** {event.get('time', '')}")
                st.write(f"**Durée:** {event.get('duration', 0)} min")
                if event.get('notes'):
                    st.write(f"**Notes:** {event.get('notes', '')}")
    else:
        st.info("Aucun événement enregistré")

# ==================== PAGE AJOUTER ÉVÉNEMENT ====================
elif current_page == "Ajouter Événement":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-plus', 'normal')}
            Ajouter un Nouvel Événement
        </h2>
    """, unsafe_allow_html=True)
    
    # Sélection du type d'événement
    event_type = st.selectbox(
        "Type d'événement",
        list(EVENT_TYPES.values())
    )
    
    col1, col2 = st.columns(2)
    with col1:
        event_date = st.date_input("Date", value=datetime.now().date())
        event_time = st.time_input("Heure", value=datetime.now().time())
    with col2:
        event_name = st.text_input("Nom de l'événement", placeholder="Ex: Séance de musculation")
        duration = st.number_input("Durée (minutes)", min_value=0, value=60, step=5)
    
    # Initialiser les variables
    session_type = None
    calories_burned = 0
    meal_calories = 0
    meal_protein = 0.0
    meal_carbs = 0.0
    meal_fats = 0.0
    bedtime = None
    wake_time = None
    quality_score = 3
    duration_hours = 0.0
    weight_kg = 0.0
    body_fat = 0.0
    muscle_mass = 0.0
    amount_liters = 0.0
    task_type = ""
    productivity_score = 3
    
    # Formulaire selon le type
    if EVENT_TYPES['SPORT'] in event_type:
        subheader_with_icon('fa-dumbbell', 'Détails de la Séance de Sport')
        
        session_type = st.selectbox("Type de séance", SPORT_SESSION_TYPES)
        
        # Onglets pour Musculation et Cardio (emojis car Streamlit ne supporte pas HTML dans les tabs)
        tab1, tab2 = st.tabs(["💪 Musculation", "🏃 Cardio"])
        
        with tab1:
            st.write("Ajouter des exercices")
            if st.button(f"{get_icon_html('fa-plus', 'small')} Ajouter un exercice", key="add_exercise"):
                st.session_state.exercises.append({
                    'name': '',
                    'sets': None,
                    'reps': None,
                    'weight': None,
                    'rest_seconds': None
                })
            
            for idx, exercise in enumerate(st.session_state.exercises):
                with st.expander(f"Exercice {idx + 1}", expanded=True):
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        exercise['name'] = st.text_input("Nom", value=exercise.get('name', ''), key=f"ex_name_{idx}")
                    with col2:
                        exercise['sets'] = st.number_input("Séries", min_value=0, value=exercise.get('sets'), key=f"ex_sets_{idx}")
                    with col3:
                        exercise['reps'] = st.number_input("Répétitions", min_value=0, value=exercise.get('reps'), key=f"ex_reps_{idx}")
                    with col4:
                        exercise['weight'] = st.number_input("Poids (kg)", min_value=0.0, value=exercise.get('weight'), key=f"ex_weight_{idx}")
                    with col5:
                        exercise['rest_seconds'] = st.number_input("Repos (sec)", min_value=0, value=exercise.get('rest_seconds'), key=f"ex_rest_{idx}")
                    
                    if st.button(f"{get_icon_html('fa-trash', 'small')} Supprimer", key=f"del_ex_{idx}"):
                        st.session_state.exercises.pop(idx)
                        st.rerun()
        
        with tab2:
            st.write("Ajouter des activités cardio")
            if st.button(f"{get_icon_html('fa-plus', 'small')} Ajouter une activité cardio", key="add_cardio"):
                st.session_state.cardio_activities.append({
                    'activity_type': '',
                    'duration': None,
                    'distance': None,
                    'calories': None
                })
            
            for idx, cardio in enumerate(st.session_state.cardio_activities):
                with st.expander(f"Activité Cardio {idx + 1}", expanded=True):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        cardio['activity_type'] = st.selectbox("Type", CARDIO_TYPES, key=f"cardio_type_{idx}")
                    with col2:
                        cardio['duration'] = st.number_input("Durée (min)", min_value=0, value=cardio.get('duration'), key=f"cardio_dur_{idx}")
                    with col3:
                        cardio['distance'] = st.number_input("Distance (km)", min_value=0.0, value=cardio.get('distance'), key=f"cardio_dist_{idx}")
                    with col4:
                        cardio['calories'] = st.number_input("Calories", min_value=0, value=cardio.get('calories'), key=f"cardio_cal_{idx}")
                    
                    if st.button(f"{get_icon_html('fa-trash', 'small')} Supprimer", key=f"del_cardio_{idx}"):
                        st.session_state.cardio_activities.pop(idx)
                        st.rerun()
        
        calories_burned = st.number_input("Calories brûlées (total)", min_value=0, value=0)
    
    elif EVENT_TYPES['MEAL'] in event_type:
        subheader_with_icon('fa-utensils', 'Détails du Repas')
        col1, col2 = st.columns(2)
        with col1:
            meal_calories = st.number_input("Calories", min_value=0, value=0)
            meal_protein = st.number_input("Protéines (g)", min_value=0.0, value=0.0)
        with col2:
            meal_carbs = st.number_input("Glucides (g)", min_value=0.0, value=0.0)
            meal_fats = st.number_input("Lipides (g)", min_value=0.0, value=0.0)
    
    elif EVENT_TYPES['SLEEP'] in event_type:
        subheader_with_icon('fa-moon', 'Détails du Sommeil')
        col1, col2 = st.columns(2)
        with col1:
            bedtime = st.time_input("Heure de coucher", value=datetime.now().time())
            wake_time = st.time_input("Heure de réveil", value=datetime.now().time())
        with col2:
            quality_score = st.slider("Qualité (1-5)", min_value=1, max_value=5, value=3)
            # Calculer la durée
            bed_dt = datetime.combine(event_date, bedtime)
            wake_dt = datetime.combine(event_date, wake_time)
            if wake_dt < bed_dt:
                wake_dt += timedelta(days=1)
            duration_hours = (wake_dt - bed_dt).total_seconds() / 3600
            st.metric("Durée", f"{duration_hours:.1f} heures")
    
    elif EVENT_TYPES['WEIGHT'] in event_type:
        subheader_with_icon('fa-weight-scale', 'Détails du Poids')
        col1, col2, col3 = st.columns(3)
        with col1:
            weight_kg = st.number_input("Poids (kg)", min_value=0.0, value=0.0)
        with col2:
            body_fat = st.number_input("Masse grasse (%)", min_value=0.0, max_value=100.0, value=0.0)
        with col3:
            muscle_mass = st.number_input("Masse musculaire (%)", min_value=0.0, max_value=100.0, value=0.0)
    
    elif EVENT_TYPES['HYDRATION'] in event_type:
        subheader_with_icon('fa-droplet', 'Détails de l\'Hydratation')
        amount_liters = st.number_input("Quantité (litres)", min_value=0.0, value=0.0, step=0.25)
    
    elif EVENT_TYPES['WORK'] in event_type:
        st.subheader("💼 Détails du Travail")
        task_type = st.text_input("Type de tâche", placeholder="Ex: Développement, Réunion, etc.")
        productivity_score = st.slider("Productivité (1-5)", min_value=1, max_value=5, value=3)
    
    notes = st.text_area("Notes", placeholder="Détails supplémentaires...")
    
    # Bouton d'ajout
    if st.button(f"{get_icon_html('fa-plus', 'small')} Ajouter l'événement", type="primary", use_container_width=True):
        event_datetime = datetime.combine(event_date, event_time)
        datetime_str = event_datetime.isoformat()
        date_str = event_date.isoformat()
        time_str = event_time.strftime("%H:%M")
        
        # Ajouter l'événement de base
        event_id = db.add_event(
            type=event_type,
            name=event_name if event_name else event_type,
            datetime_str=datetime_str,
            date_str=date_str,
            time_str=time_str,
            duration=duration,
            notes=notes
        )
        
        # Ajouter les données spécifiques
        if EVENT_TYPES['SPORT'] in event_type:
            session_id = db.add_sport_session(
                event_id=event_id,
                session_type=session_type,
                total_duration=duration,
                calories_burned=calories_burned
            )
            
            # Ajouter les exercices
            for idx, exercise in enumerate(st.session_state.exercises):
                if exercise.get('name'):
                    db.add_exercise(
                        session_id=session_id,
                        name=exercise['name'],
                        sets=exercise.get('sets'),
                        reps=exercise.get('reps'),
                        weight=exercise.get('weight'),
                        rest_seconds=exercise.get('rest_seconds'),
                        exercise_order=idx
                    )
            
            # Ajouter les activités cardio
            for cardio in st.session_state.cardio_activities:
                if cardio.get('activity_type'):
                    db.add_cardio_activity(
                        session_id=session_id,
                        activity_type=cardio.get('activity_type'),
                        duration=cardio.get('duration'),
                        distance=cardio.get('distance'),
                        calories=cardio.get('calories')
                    )
            
            # Réinitialiser les listes
            st.session_state.exercises = []
            st.session_state.cardio_activities = []
        
        elif EVENT_TYPES['MEAL'] in event_type:
            db.add_meal(
                event_id=event_id,
                name=event_name,
                calories=meal_calories,
                protein=meal_protein,
                carbs=meal_carbs,
                fats=meal_fats
            )
        
        elif EVENT_TYPES['SLEEP'] in event_type:
            db.add_sleep_record(
                event_id=event_id,
                bedtime=bedtime.strftime("%H:%M") if bedtime else None,
                wake_time=wake_time.strftime("%H:%M") if wake_time else None,
                duration_hours=duration_hours,
                quality_score=quality_score
            )
        
        elif EVENT_TYPES['WEIGHT'] in event_type:
            db.add_weight_record(
                event_id=event_id,
                weight_kg=weight_kg,
                body_fat_percent=body_fat,
                muscle_mass_percent=muscle_mass
            )
        
        elif EVENT_TYPES['HYDRATION'] in event_type:
            db.add_hydration_record(
                event_id=event_id,
                amount_liters=amount_liters
            )
        
        elif EVENT_TYPES['WORK'] in event_type:
            db.add_work_session(
                event_id=event_id,
                task_type=task_type,
                productivity_score=productivity_score
            )
        
        st.success(f"✅ Événement '{event_name if event_name else event_type}' ajouté avec succès!")
        st.balloons()
        st.rerun()

# ==================== PAGE TABLEAU DE BORD ====================
elif current_page == "Tableau de Bord":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-chart-line', 'normal')}
            Tableau de Bord
        </h2>
    """, unsafe_allow_html=True)
    
    events = db.get_all_events()
    
    if not events:
        st.info("📝 Aucun événement enregistré. Commencez par ajouter un événement!")
    else:
        # Filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            event_types = ["Tous"] + list(set([e.get('type', '') for e in events]))
            filter_type = st.selectbox("Filtrer par type", event_types)
        
        with col2:
            date_range = st.selectbox(
                "Période",
                ["Aujourd'hui", "Cette semaine", "Ce mois", "Tout"]
            )
        
        with col3:
            sort_by = st.selectbox(
                "Trier par",
                ["Date (récent)", "Date (ancien)", "Type", "Durée"]
            )
        
        # Filtrage
        filtered_events = events.copy()
        
        if filter_type != "Tous":
            filtered_events = [e for e in filtered_events if e.get('type') == filter_type]
        
        today = datetime.now().date()
        if date_range == "Aujourd'hui":
            today_str = today.isoformat()
            filtered_events = [e for e in filtered_events if e.get('date') == today_str]
        elif date_range == "Cette semaine":
            week_start = today - timedelta(days=today.weekday())
            filtered_events = [e for e in filtered_events if datetime.fromisoformat(e.get('date', '2000-01-01')).date() >= week_start]
        elif date_range == "Ce mois":
            month_start = today.replace(day=1)
            filtered_events = [e for e in filtered_events if datetime.fromisoformat(e.get('date', '2000-01-01')).date() >= month_start]
        
        # Tri
        if sort_by == "Date (récent)":
            filtered_events.sort(key=lambda x: x.get('datetime', ''), reverse=True)
        elif sort_by == "Date (ancien)":
            filtered_events.sort(key=lambda x: x.get('datetime', ''))
        elif sort_by == "Type":
            filtered_events.sort(key=lambda x: x.get('type', ''))
        elif sort_by == "Durée":
            filtered_events.sort(key=lambda x: x.get('duration', 0), reverse=True)
        
        # Affichage
        subheader_with_icon('fa-clipboard-list', f'Événements ({len(filtered_events)})')
        
        for event in filtered_events:
            event_dt = datetime.fromisoformat(event.get('datetime', datetime.now().isoformat()))
            with st.expander(f"{event.get('type', '')} - {event.get('name', '')} | {event_dt.strftime('%d/%m/%Y %H:%M')}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Durée", f"{event.get('duration', 0)} min")
                with col2:
                    st.write(f"**Date:** {event.get('date', '')}")
                with col3:
                    st.write(f"**Heure:** {event.get('time', '')}")
                
                # Afficher les données spécifiques
                if 'sport_data' in event and event['sport_data']:
                    sport = event['sport_data']
                    st.write("**Séance de sport:**")
                    if sport.get('exercises'):
                        st.write("Exercices:")
                        for ex in sport['exercises']:
                            st.write(f"- {ex.get('name', '')}: {ex.get('sets', 0)}x{ex.get('reps', 0)} @ {ex.get('weight', 0)}kg")
                    if sport.get('cardio'):
                        st.write("Cardio:")
                        for c in sport['cardio']:
                            st.write(f"- {c.get('activity_type', '')}: {c.get('duration', 0)}min")
                
                if 'meal_data' in event and event['meal_data']:
                    meal = event['meal_data']
                    st.write(f"**Repas:** {meal.get('calories', 0)} kcal | P: {meal.get('protein', 0)}g | C: {meal.get('carbs', 0)}g | F: {meal.get('fats', 0)}g")
                
                if event.get('notes'):
                    st.write(f"**Notes:** {event.get('notes', '')}")
                
                if st.button(f"{get_icon_html('fa-trash', 'small')} Supprimer", key=f"delete_{event.get('id')}"):
                    db.delete_event(event.get('id'))
                    st.rerun()

# ==================== PAGE STATISTIQUES ====================
elif current_page == "Statistiques":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-chart-bar', 'normal')}
            Statistiques et Analyses
        </h2>
    """, unsafe_allow_html=True)
    
    events = db.get_all_events()
    
    if not events:
        st.info("📝 Aucune donnée disponible. Ajoutez des événements pour voir les statistiques!")
    else:
        # Statistiques générales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Événements", len(events))
        
        with col2:
            total_duration = sum([e.get('duration', 0) for e in events])
            st.metric("Temps Total", f"{total_duration // 60}h {total_duration % 60}min")
        
        with col3:
            sport_events = [e for e in events if 'Sport' in e.get('type', '')]
            st.metric("Séances Sport", len(sport_events))
        
        with col4:
            today_sport = get_today_sport_count()
            st.metric("Sport Aujourd'hui", f"{today_sport}/{DEFAULT_SPORT_SESSIONS_PER_DAY}")
        
        st.markdown("---")
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            subheader_with_icon('fa-chart-line', 'Événements par Type')
            type_counts = pd.Series([e.get('type', '') for e in events]).value_counts()
            fig_pie = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Distribution des Types d'Événements"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            subheader_with_icon('fa-chart-bar', 'Événements par Jour')
            df = pd.DataFrame(events)
            df['date'] = pd.to_datetime(df['date'])
            df['date_only'] = df['date'].dt.date
            daily_counts = df.groupby('date_only').size().reset_index(name='count')
            daily_counts = daily_counts.sort_values('date_only')
            fig_bar = px.bar(
                daily_counts,
                x='date_only',
                y='count',
                title="Nombre d'Événements par Jour",
                labels={'date_only': 'Date', 'count': 'Nombre'}
            )
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Graphique des séances de sport
        st.subheader("🏋️ Suivi des Séances de Sport")
        sport_df = pd.DataFrame(sport_events)
        
        if not sport_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                sport_df['date'] = pd.to_datetime(sport_df['date'])
                sport_df['date_only'] = sport_df['date'].dt.date
                sport_daily = sport_df.groupby('date_only').size().reset_index(name='séances')
                sport_daily = sport_daily.sort_values('date_only')
                
                fig_sport = px.line(
                    sport_daily,
                    x='date_only',
                    y='séances',
                    title="Séances de Sport par Jour",
                    markers=True
                )
                fig_sport.add_hline(
                    y=DEFAULT_SPORT_SESSIONS_PER_DAY,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Objectif: {DEFAULT_SPORT_SESSIONS_PER_DAY} séances/jour"
                )
                st.plotly_chart(fig_sport, use_container_width=True)
            
            with col2:
                sport_stats = calculate_sport_statistics(events)
                st.metric("Temps Total Sport", f"{sport_stats['total_duration'] // 60}h {sport_stats['total_duration'] % 60}min")
                st.metric("Durée Moyenne", f"{int(sport_stats['avg_duration'])} min")
                st.metric("Calories Totales", f"{sport_stats['total_calories']} kcal")
                
                today = datetime.now().date()
                today_sport_count = len([e for e in sport_events if datetime.fromisoformat(e.get('date', '2000-01-01')).date() == today])
                progress = min(today_sport_count / DEFAULT_SPORT_SESSIONS_PER_DAY, 1.0)
                st.metric("Séances Aujourd'hui", f"{today_sport_count}/{DEFAULT_SPORT_SESSIONS_PER_DAY}")
                st.progress(progress)
        else:
            st.info("Aucune séance de sport enregistrée")
        
        # Statistiques scolaires
        st.markdown("---")
        st.subheader("🏫 Statistiques Scolaires")
        
        exams = db.get_all_exams()
        courses = db.get_all_courses()
        assignments = db.get_all_assignments()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Examens", len(exams))
        with col2:
            upcoming_exams = db.get_upcoming_exams(days=30)
            st.metric("Examens à Venir (30j)", len(upcoming_exams))
        with col3:
            st.metric("Cours", len(courses))
        with col4:
            pending_assignments = [a for a in assignments if a.get('status') != 'completed']
            st.metric("Devoirs en Attente", len(pending_assignments))
        
        # Graphiques scolaires
        col1, col2 = st.columns(2)
        
        with col1:
            if exams:
                subheader_with_icon('fa-book', 'Examens par Matière')
                exam_df = pd.DataFrame(exams)
                if 'subject' in exam_df.columns:
                    subject_counts = exam_df['subject'].value_counts()
                    if len(subject_counts) > 0:
                        fig = px.bar(
                            x=subject_counts.index,
                            y=subject_counts.values,
                            title="Examens par Matière",
                            labels={'x': 'Matière', 'y': 'Nombre'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if assignments:
                subheader_with_icon('fa-file-lines', 'Devoirs par Statut')
                assign_df = pd.DataFrame(assignments)
                if 'status' in assign_df.columns:
                    status_counts = assign_df['status'].value_counts()
                    if len(status_counts) > 0:
                        fig = px.pie(
                            values=status_counts.values,
                            names=status_counts.index,
                            title="Distribution des Statuts"
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        # Analyses avancées
        st.markdown("---")
        subheader_with_icon('fa-chart-line', 'Analyses Avancées')
        
        from analytics import analyze_study_time, analyze_productivity, analyze_habits, analyze_goals_progress
        
        tab1, tab2, tab3, tab4 = st.tabs(["📚 Temps d'Étude", "⚡ Productivité", "🔄 Habitudes", "🎯 Objectifs"])
        
        with tab1:
            study_analysis = analyze_study_time(events, days=30)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Temps Total", f"{study_analysis['total_hours']:.1f}h")
            with col2:
                st.metric("Moyenne Quotidienne", f"{study_analysis['avg_daily_hours']:.1f}h")
            with col3:
                trend_icon = "📈" if study_analysis['trend'] == 'increasing' else "📉" if study_analysis['trend'] == 'decreasing' else "➡️"
                st.metric("Tendance", trend_icon)
            
            if study_analysis['daily_breakdown']:
                daily_df = pd.DataFrame(study_analysis['daily_breakdown'])
                fig = px.line(
                    daily_df,
                    x='date_only',
                    y='hours',
                    title="Temps d'Étude par Jour",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            productivity_analysis = analyze_productivity(events, days=30)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Score Moyen", f"{productivity_analysis['avg_score']:.1f}/5")
                if productivity_analysis['correlation_sleep']:
                    st.metric("Corrélation Sommeil", f"{productivity_analysis['correlation_sleep']:.2f}")
            with col2:
                trend_icon = "📈" if productivity_analysis['trend'] == 'increasing' else "📉" if productivity_analysis['trend'] == 'decreasing' else "➡️"
                st.metric("Tendance", trend_icon)
            
            if productivity_analysis['scores_by_date']:
                scores_df = pd.DataFrame(productivity_analysis['scores_by_date'])
                fig = px.line(
                    scores_df,
                    x='date',
                    y='avg_score',
                    title="Productivité dans le Temps",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            habit_type = st.selectbox("Type d'habitude", ["sport", "sleep"], key="habit_type")
            habit_analysis = analyze_habits(events, habit_type=habit_type, days=30)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Score de Consistance", f"{habit_analysis['consistency_score']:.2f}")
            with col2:
                st.metric("Fréquence", f"{habit_analysis['frequency']:.1%}")
            
            if habit_analysis['patterns']:
                patterns_df = pd.DataFrame(list(habit_analysis['patterns'].items()), columns=['Jour', 'Fréquence'])
                patterns_df['Jour'] = patterns_df['Jour'].map(lambda x: WEEKDAYS[x])
                fig = px.bar(patterns_df, x='Jour', y='Fréquence', title=f"Patterns - {habit_type}")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            objectives = db.get_all_objectives()
            goals_analysis = analyze_goals_progress(objectives, events)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Objectifs", goals_analysis['total_objectives'])
            with col2:
                st.metric("Complétés", goals_analysis['completed'])
            with col3:
                st.metric("En Cours", goals_analysis['in_progress'])
            
            if goals_analysis['progress_details']:
                for detail in goals_analysis['progress_details']:
                    st.write(f"**{detail['name']}:** {detail['current']:.1f}/{detail['target']:.1f}")
                    st.progress(detail['progress'])

# ==================== PAGE OBJECTIFS ====================
elif current_page == "Objectifs":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-bullseye', 'normal')}
            Objectifs
        </h2>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Mes Objectifs", "➕ Créer un Objectif"])
    
    with tab1:
        objectives = db.get_all_objectives(status='active')
        
        if not objectives:
            st.info("Aucun objectif actif. Créez-en un dans l'onglet 'Créer un Objectif'")
        else:
            for obj in objectives:
                with st.expander(f"{obj.get('name', '')} - {obj.get('type', '')}", expanded=True):
                    current = obj.get('current_value', 0) or 0
                    target = obj.get('target_value', 0) or 1
                    progress = min(current / target, 1.0) if target > 0 else 0
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.metric("Progression", f"{current:.1f} / {target:.1f}")
                        st.progress(progress)
                    with col2:
                        if st.button(f"{get_icon_html('fa-check', 'small')} Complété", key=f"complete_{obj.get('id')}"):
                            db.update_objective(obj.get('id'), status='completed')
                            st.rerun()
                        if st.button(f"{get_icon_html('fa-xmark', 'small')} Annuler", key=f"cancel_{obj.get('id')}"):
                            db.update_objective(obj.get('id'), status='cancelled')
                            st.rerun()
                    
                    st.write(f"**Fréquence:** {obj.get('frequency', 'N/A')}")
                    if obj.get('deadline'):
                        st.write(f"**Échéance:** {obj.get('deadline', '')}")
    
    with tab2:
        st.subheader("Créer un Nouvel Objectif")
        
        obj_type = st.selectbox("Type d'objectif", OBJECTIVE_TYPES)
        obj_name = st.text_input("Nom de l'objectif", placeholder="Ex: Perdre 5kg")
        target_value = st.number_input("Valeur cible", min_value=0.0, value=0.0)
        frequency = st.selectbox("Fréquence", OBJECTIVE_FREQUENCIES)
        deadline = st.date_input("Date limite (optionnel)", value=None)
        
        if st.button(f"{get_icon_html('fa-plus', 'small')} Créer l'objectif", type="primary"):
            deadline_str = deadline.isoformat() if deadline else None
            db.add_objective(
                type=obj_type,
                name=obj_name,
                target_value=target_value,
                deadline=deadline_str,
                frequency=frequency
            )
            st.success(f"✅ Objectif '{obj_name}' créé avec succès!")
            st.rerun()

# ==================== PAGE CALENDRIER ====================
elif current_page == "Calendrier":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-calendar', 'normal')}
            Vue Calendrier
        </h2>
    """, unsafe_allow_html=True)
    
    events = db.get_all_events()
    exams = db.get_all_exams()
    courses = db.get_all_courses()
    assignments = db.get_all_assignments()
    
    selected_month = st.date_input(
        "Sélectionner un mois",
        value=datetime.now().date().replace(day=1),
        key="calendar_month"
    )
    
    month_start = selected_month.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1)
    
    # Filtrer les événements du mois
    month_events = [
        e for e in events
        if month_start <= datetime.fromisoformat(e.get('date', '2000-01-01')).date() < month_end
    ]
    
    # Filtrer les examens du mois
    month_exams = [
        e for e in exams
        if month_start <= datetime.fromisoformat(e.get('exam_date', '2000-01-01')).date() < month_end
    ]
    
    # Filtrer les devoirs du mois
    month_assignments = [
        a for a in assignments
        if a.get('due_date') and month_start <= datetime.fromisoformat(a.get('due_date', '2000-01-01')).date() < month_end
    ]
    
    # Organiser par jour
    events_by_day = {}
    for event in month_events:
        event_date = datetime.fromisoformat(event.get('date', '2000-01-01')).date()
        if event_date not in events_by_day:
            events_by_day[event_date] = {'events': [], 'exams': [], 'assignments': [], 'courses': []}
        events_by_day[event_date]['events'].append(event)
    
    for exam in month_exams:
        exam_date = datetime.fromisoformat(exam.get('exam_date', '2000-01-01')).date()
        if exam_date not in events_by_day:
            events_by_day[exam_date] = {'events': [], 'exams': [], 'assignments': [], 'courses': []}
        events_by_day[exam_date]['exams'].append(exam)
    
    for assignment in month_assignments:
        due_date = datetime.fromisoformat(assignment.get('due_date', '2000-01-01')).date()
        if due_date not in events_by_day:
            events_by_day[due_date] = {'events': [], 'exams': [], 'assignments': [], 'courses': []}
        events_by_day[due_date]['assignments'].append(assignment)
    
    # Ajouter les cours récurrents
    for course in courses:
        day_of_week = course.get('day_of_week')
        if day_of_week is not None:
            # Trouver toutes les dates de ce jour dans le mois
            current_date = month_start
            while current_date < month_end:
                if current_date.weekday() == day_of_week:
                    if current_date not in events_by_day:
                        events_by_day[current_date] = {'events': [], 'exams': [], 'assignments': [], 'courses': []}
                    events_by_day[current_date]['courses'].append(course)
                current_date += timedelta(days=1)
    
    st.subheader(f"Calendrier - {selected_month.strftime('%B %Y')}")
    
    # Créer un DataFrame avec toutes les informations
    calendar_data = []
    for date, items in events_by_day.items():
        total = len(items['events']) + len(items['exams']) + len(items['assignments']) + len(items['courses'])
        types_list = []
        if items['events']:
            types_list.append(f"📅 {len(items['events'])} événement(s)")
        if items['exams']:
            types_list.append(f"📚 {len(items['exams'])} examen(s)")
        if items['assignments']:
            types_list.append(f"📝 {len(items['assignments'])} devoir(s)")
        if items['courses']:
            types_list.append(f"📖 {len(items['courses'])} cours")
        
        calendar_data.append({
            'Date': date.strftime('%d/%m/%Y'),
            'Total': total,
            'Détails': ' | '.join(types_list)
        })
    
    if calendar_data:
        calendar_df = pd.DataFrame(calendar_data)
        calendar_df = calendar_df.sort_values('Date')
        st.dataframe(calendar_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("Détails par Jour")
        selected_day = st.date_input("Sélectionner un jour", value=datetime.now().date())
        
        day_items = events_by_day.get(selected_day, {'events': [], 'exams': [], 'assignments': [], 'courses': []})
        
        if day_items['events'] or day_items['exams'] or day_items['assignments'] or day_items['courses']:
            # Événements
            if day_items['events']:
                st.write("**📅 Événements:**")
                for event in sorted(day_items['events'], key=lambda x: x.get('time', '')):
                    with st.expander(f"📅 {event.get('time', '')} - {event.get('type', '')} - {event.get('name', '')}"):
                        st.write(f"**Durée:** {event.get('duration', 0)} minutes")
                        if event.get('notes'):
                            st.write(f"**Notes:** {event.get('notes', '')}")
            
            # Examens
            if day_items['exams']:
                st.write("**📚 Examens:**")
                for exam in day_items['exams']:
                    with st.expander(f"📚 {exam.get('exam_time', '')} - {exam.get('name', '')} - {exam.get('subject', '')}"):
                        st.write(f"**Lieu:** {exam.get('location', 'N/A')}")
                        if exam.get('notes'):
                            st.write(f"**Notes:** {exam.get('notes', '')}")
            
            # Devoirs
            if day_items['assignments']:
                st.write("**📝 Devoirs (deadline):**")
                for assign in day_items['assignments']:
                    priority = PRIORITIES.get(assign.get('priority', 3), '🟡')
                    with st.expander(f"{priority} {assign.get('title', '')} - {assign.get('due_time', '')}"):
                        st.write(f"**Statut:** {assign.get('status', 'pending')}")
                        if assign.get('description'):
                            st.write(f"**Description:** {assign.get('description', '')}")
            
            # Cours
            if day_items['courses']:
                st.write("**📖 Cours:**")
                for course in day_items['courses']:
                    with st.expander(f"📖 {course.get('start_time', '')} - {course.get('name', '')} - {course.get('subject', '')}"):
                        st.write(f"**Heure:** {course.get('start_time', '')} - {course.get('end_time', '')}")
                        st.write(f"**Lieu:** {course.get('location', 'N/A')}")
                        st.write(f"**Professeur:** {course.get('teacher', 'N/A')}")
        else:
            st.info(f"Aucun événement le {selected_day.strftime('%d/%m/%Y')}")
    else:
        st.info("Aucun événement ce mois")

# ==================== PAGE EXPORT ====================
elif current_page == "Export":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-download', 'normal')}
            Export des Données
        </h2>
    """, unsafe_allow_html=True)
    
    events = db.get_all_events()
    
    if not events:
        st.info("Aucune donnée à exporter")
    else:
        # Filtres pour l'export
        col1, col2 = st.columns(2)
        with col1:
            export_type = st.selectbox("Type d'export", ["CSV", "Excel", "PDF"])
        with col2:
            date_range_export = st.selectbox(
                "Période",
                ["Tout", "Cette semaine", "Ce mois", "Personnalisé"]
            )
        
        # Filtrage
        events_to_export = events.copy()
        
        if date_range_export == "Cette semaine":
            week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).date()
            events_to_export = [e for e in events_to_export if datetime.fromisoformat(e.get('date', '2000-01-01')).date() >= week_start]
        elif date_range_export == "Ce mois":
            month_start = datetime.now().date().replace(day=1)
            events_to_export = [e for e in events_to_export if datetime.fromisoformat(e.get('date', '2000-01-01')).date() >= month_start]
        elif date_range_export == "Personnalisé":
            start_date = st.date_input("Date de début")
            end_date = st.date_input("Date de fin")
            events_to_export = [
                e for e in events_to_export
                if start_date <= datetime.fromisoformat(e.get('date', '2000-01-01')).date() <= end_date
            ]
        
        st.write(f"**{len(events_to_export)} événements** seront exportés")
        
        if st.button("📥 Télécharger", type="primary"):
            if export_type == "CSV":
                csv_data = export_to_csv(events_to_export)
                st.download_button(
                    label="Télécharger CSV",
                    data=csv_data,
                    file_name=f"events_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            elif export_type == "Excel":
                excel_data = export_to_excel(events_to_export)
                st.download_button(
                    label="Télécharger Excel",
                    data=excel_data,
                    file_name=f"events_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif export_type == "PDF":
                pdf_data = export_to_pdf(events_to_export, period=date_range_export)
                st.download_button(
                    label="Télécharger PDF",
                    data=pdf_data,
                    file_name=f"events_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )

# ==================== PAGE RAPPELS ====================
elif current_page == "Rappels":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-bell', 'normal')}
            Gestion des Rappels
        </h2>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Mes Rappels", "➕ Créer un Rappel"])
    
    with tab1:
        reminders = db.get_all_reminders(enabled_only=False)
        
        if not reminders:
            st.info("Aucun rappel configuré. Créez-en un dans l'onglet 'Créer un Rappel'")
        else:
            for reminder in reminders:
                enabled = reminder.get('enabled', 0) == 1
                status = "✅ Actif" if enabled else "❌ Inactif"
                
                with st.expander(f"{reminder.get('type', '')} - {status}", expanded=True):
                    st.write(f"**Message:** {reminder.get('message', '')}")
                    st.write(f"**Heure:** {reminder.get('time', '')}")
                    st.write(f"**Fréquence:** {reminder.get('frequency', '')}")
                    
                    if enabled:
                        if st.button("Désactiver", key=f"disable_{reminder.get('id')}"):
                            db.toggle_reminder(reminder.get('id'), False)
                            st.rerun()
                    else:
                        if st.button("Activer", key=f"enable_{reminder.get('id')}"):
                            db.toggle_reminder(reminder.get('id'), True)
                            st.rerun()
                    
                    if st.button(f"{get_icon_html('fa-trash', 'small')} Supprimer", key=f"delete_rem_{reminder.get('id')}"):
                        db.delete_reminder(reminder.get('id'))
                        st.rerun()
    
    with tab2:
        st.subheader("Créer un Nouveau Rappel")
        
        rem_type = st.selectbox("Type de rappel", REMINDER_TYPES)
        rem_message = st.text_input("Message", placeholder="Ex: N'oublie pas ta séance de sport!")
        rem_time = st.time_input("Heure", value=datetime.now().time())
        rem_frequency = st.selectbox("Fréquence", REMINDER_FREQUENCIES)
        
        if st.button(f"{get_icon_html('fa-plus', 'small')} Créer le rappel", type="primary"):
            time_str = rem_time.strftime("%H:%M")
            db.add_reminder(
                type=rem_type,
                message=rem_message,
                time=time_str,
                frequency=rem_frequency
            )
            st.success(f"✅ Rappel créé avec succès!")
            st.rerun()

# ==================== PAGE ÉCOLE ====================
elif current_page == "École":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-school', 'normal')}
            Gestion Scolaire
        </h2>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 Examens",
        "📖 Cours",
        "📝 Devoirs",
        "🍱 Rappel Tupperware"
    ])
    
    with tab1:
        subheader_with_icon('fa-book', 'Gestion des Examens')
        
        # Ajouter un examen
        with st.expander("➕ Ajouter un Examen", expanded=False):
            exam_name = st.text_input("Nom de l'examen", key="exam_name")
            exam_subject = st.text_input("Matière", key="exam_subject")
            col1, col2 = st.columns(2)
            with col1:
                exam_date = st.date_input("Date", key="exam_date")
            with col2:
                exam_time = st.time_input("Heure", key="exam_time")
            exam_location = st.text_input("Lieu", key="exam_location")
            exam_notes = st.text_area("Notes", key="exam_notes")
            reminder_days = st.number_input("Rappel (jours avant)", min_value=0, max_value=7, value=1, key="reminder_days")
            
            if st.button(f"{get_icon_html('fa-plus', 'small')} Ajouter l'examen", key="add_exam_btn"):
                exam_datetime_str = datetime.combine(exam_date, exam_time).isoformat()
                exam_id = db.add_exam(
                    name=exam_name,
                    subject=exam_subject,
                    exam_date=exam_date.isoformat(),
                    exam_time=exam_time.strftime("%H:%M"),
                    location=exam_location,
                    notes=exam_notes,
                    reminder_days_before=reminder_days
                )
                
                # Créer un rappel intelligent
                reminder_time = (datetime.combine(exam_date, exam_time) - timedelta(days=reminder_days)).isoformat()
                db.add_smart_reminder(
                    event_type="exam",
                    event_id=exam_id,
                    reminder_type="exam_reminder",
                    reminder_time=reminder_time,
                    message=f"Rappel : Examen {exam_name} dans {reminder_days} jour(s)",
                    notification_method="both"
                )
                
                st.success(f"{get_icon_html('fa-check', 'small')} Examen '{exam_name}' ajouté avec rappel configuré!")
                st.rerun()
        
        # Statistiques
        subheader_with_icon('fa-chart-line', 'Statistiques')
        all_exams = db.get_all_exams()
        upcoming_exams = db.get_upcoming_exams(days=30)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Examens", len(all_exams))
        with col2:
            st.metric("À Venir (30j)", len(upcoming_exams))
        with col3:
            subjects = [e.get('subject', 'N/A') for e in all_exams if e.get('subject')]
            unique_subjects = len(set(subjects)) if subjects else 0
            st.metric("Matières", unique_subjects)
        with col4:
            if upcoming_exams:
                next_exam_date = datetime.fromisoformat(upcoming_exams[0].get('exam_date', datetime.now().isoformat())).date()
                days_until = (next_exam_date - datetime.now().date()).days
                st.metric("Prochain Examen", f"{days_until} jours")
            else:
                st.metric("Prochain Examen", "N/A")
        
        # Graphique par matière
        if all_exams:
            st.markdown("---")
            exam_df = pd.DataFrame(all_exams)
            if 'subject' in exam_df.columns:
                subject_counts = exam_df['subject'].value_counts()
                if len(subject_counts) > 0:
                    fig = px.bar(
                        x=subject_counts.index,
                        y=subject_counts.values,
                        title="Examens par Matière",
                        labels={'x': 'Matière', 'y': 'Nombre d\'examens'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Filtres
        subheader_with_icon('fa-clipboard-list', 'Liste des Examens')
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_type = st.selectbox("Filtrer", ["Tous", "À venir", "Passés"])
        with col2:
            all_subjects = ["Toutes"] + list(set([e.get('subject', '') for e in all_exams if e.get('subject')]))
            filter_subject = st.selectbox("Matière", all_subjects)
        with col3:
            date_range = st.selectbox("Période", ["Tout", "Cette semaine", "Ce mois", "30 jours"])
        
        # Filtrage
        exams = all_exams.copy()
        if filter_type == "À venir":
            exams = [e for e in exams if datetime.fromisoformat(e.get('exam_date', '2000-01-01')).date() >= datetime.now().date()]
        elif filter_type == "Passés":
            exams = [e for e in exams if datetime.fromisoformat(e.get('exam_date', '2000-01-01')).date() < datetime.now().date()]
        
        if filter_subject != "Toutes":
            exams = [e for e in exams if e.get('subject') == filter_subject]
        
        if date_range == "Cette semaine":
            week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).date()
            week_end = week_start + timedelta(days=6)
            exams = [e for e in exams if week_start <= datetime.fromisoformat(e.get('exam_date', '2000-01-01')).date() <= week_end]
        elif date_range == "Ce mois":
            month_start = datetime.now().date().replace(day=1)
            exams = [e for e in exams if datetime.fromisoformat(e.get('exam_date', '2000-01-01')).date() >= month_start]
        elif date_range == "30 jours":
            future_date = (datetime.now().date() + timedelta(days=30))
            exams = [e for e in exams if datetime.fromisoformat(e.get('exam_date', '2000-01-01')).date() <= future_date]
        
        if exams:
            for exam in exams:
                exam_date_obj = datetime.fromisoformat(exam.get('exam_date', datetime.now().isoformat()))
                days_until = (exam_date_obj.date() - datetime.now().date()).days
                status_icon = "🔴" if days_until < 7 else "🟡" if days_until < 30 else "🟢"
                
                with st.expander(f"{status_icon} {exam.get('name', '')} - {exam.get('subject', '')} | {exam_date_obj.strftime('%d/%m/%Y')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Date:** {exam.get('exam_date', '')}")
                        st.write(f"**Heure:** {exam.get('exam_time', '')}")
                        st.write(f"**Lieu:** {exam.get('location', 'N/A')}")
                        st.write(f"**Rappel:** {exam.get('reminder_days_before', 1)} jour(s) avant")
                    with col2:
                        st.metric("Jours restants", days_until)
                        if exam.get('notes'):
                            st.write(f"**Notes:** {exam.get('notes', '')}")
                    
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        if st.button("✏️ Modifier", key=f"edit_exam_{exam.get('id')}"):
                            st.session_state[f"editing_exam_{exam.get('id')}"] = True
                    with col4:
                        if st.button("🔔 Tester Notification", key=f"test_notif_{exam.get('id')}"):
                            result = send_exam_reminder(
                                exam_name=exam.get('name', ''),
                                exam_date=exam_date_obj,
                                days_before=exam.get('reminder_days_before', 1)
                            )
                            if result.get('email') or result.get('telegram'):
                                st.success("Notification envoyée!")
                            else:
                                st.warning("Notifications non configurées. Voir Configuration.")
                    with col5:
                        if st.button("🗑️ Supprimer", key=f"del_exam_{exam.get('id')}"):
                            db.delete_exam(exam.get('id'))
                            st.rerun()
        else:
            st.info("Aucun examen trouvé avec ces filtres")
    
    with tab2:
        st.subheader("📖 Gestion des Cours")
        
        # Ajouter un cours
        with st.expander("➕ Ajouter un Cours", expanded=False):
            course_name = st.text_input("Nom du cours", key="course_name")
            course_subject = st.text_input("Matière", key="course_subject")
            col1, col2 = st.columns(2)
            with col1:
                day_of_week = st.selectbox("Jour", options=list(range(7)), format_func=lambda x: WEEKDAYS[x], key="course_day")
            with col2:
                course_location = st.text_input("Lieu", key="course_location")
            col3, col4 = st.columns(2)
            with col3:
                start_time = st.time_input("Heure début", key="start_time")
            with col4:
                end_time = st.time_input("Heure fin", key="end_time")
            teacher = st.text_input("Professeur", key="teacher")
            course_notes = st.text_area("Notes", key="course_notes")
            tupperware_reminder = st.checkbox("Rappel Tupperware la veille", value=True, key="tupperware_check")
            
            if st.button("➕ Ajouter le cours", key="add_course_btn"):
                course_id = db.add_course(
                    name=course_name,
                    subject=course_subject,
                    day_of_week=day_of_week,
                    start_time=start_time.strftime("%H:%M"),
                    end_time=end_time.strftime("%H:%M"),
                    location=course_location,
                    teacher=teacher,
                    notes=course_notes,
                    tupperware_reminder=1 if tupperware_reminder else 0
                )
                st.success(f"✅ Cours '{course_name}' ajouté!")
                st.rerun()
        
        # Vue hebdomadaire
        st.subheader("📅 Emploi du Temps Hebdomadaire")
        courses_by_day = db.get_courses_for_week()
        
        if courses_by_day:
            # Créer un tableau pour l'emploi du temps
            schedule_data = []
            for day in range(7):
                day_name = WEEKDAYS[day]
                day_courses = courses_by_day.get(day, [])
                if day_courses:
                    for course in day_courses:
                        schedule_data.append({
                            'Jour': day_name,
                            'Cours': course.get('name', ''),
                            'Matière': course.get('subject', ''),
                            'Heure': f"{course.get('start_time', '')} - {course.get('end_time', '')}",
                            'Lieu': course.get('location', 'N/A'),
                            'Professeur': course.get('teacher', 'N/A')
                        })
            
            if schedule_data:
                schedule_df = pd.DataFrame(schedule_data)
                st.dataframe(schedule_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Liste des cours
        subheader_with_icon('fa-clipboard-list', 'Mes Cours')
        courses = db.get_all_courses()
        
        if courses:
            for course in courses:
                day_name = WEEKDAYS[course.get('day_of_week', 0)] if course.get('day_of_week') is not None else "N/A"
                with st.expander(f"📖 {course.get('name', '')} - {day_name}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Matière:** {course.get('subject', '')}")
                        st.write(f"**Heure:** {course.get('start_time', '')} - {course.get('end_time', '')}")
                        st.write(f"**Lieu:** {course.get('location', 'N/A')}")
                    with col2:
                        st.write(f"**Professeur:** {course.get('teacher', 'N/A')}")
                        if course.get('tupperware_reminder'):
                            st.success("🍱 Rappel Tupperware activé")
                        if course.get('notes'):
                            st.write(f"**Notes:** {course.get('notes', '')}")
                    
                    # Afficher les devoirs liés
                    assignments = db.get_assignments_by_course(course.get('id'))
                    if assignments:
                        st.write("**Devoirs liés:**")
                        for assign in assignments[:5]:  # Limiter à 5
                            status_icon = "✅" if assign.get('status') == 'completed' else "⏳"
                            st.write(f"{status_icon} {assign.get('title', '')} - {assign.get('due_date', '')}")
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        if st.button("✏️ Modifier", key=f"edit_course_{course.get('id')}"):
                            st.session_state[f"editing_course_{course.get('id')}"] = True
                    with col4:
                        if st.button("🗑️ Supprimer", key=f"del_course_{course.get('id')}"):
                            db.delete_course(course.get('id'))
                            st.rerun()
        else:
            st.info("Aucun cours enregistré")
    
    with tab3:
        subheader_with_icon('fa-file-lines', 'Gestion des Devoirs')
        
        # Ajouter un devoir
        with st.expander("➕ Ajouter un Devoir", expanded=False):
            assignment_title = st.text_input("Titre", key="assign_title")
            courses = db.get_all_courses()
            course_options = {0: "Aucun"}
            course_options.update({c.get('id'): c.get('name') for c in courses})
            selected_course_id = st.selectbox("Cours associé", options=list(course_options.keys()), 
                                              format_func=lambda x: course_options[x], key="assign_course")
            col1, col2 = st.columns(2)
            with col1:
                due_date = st.date_input("Date limite", key="assign_date")
            with col2:
                due_time = st.time_input("Heure limite", key="assign_time")
            description = st.text_area("Description", key="assign_desc")
            priority = st.slider("Priorité", min_value=1, max_value=4, value=3, key="assign_priority")
            st.write(f"Priorité: {PRIORITIES[priority]}")
            
            if st.button("➕ Ajouter le devoir", key="add_assign_btn"):
                assignment_id = db.add_assignment(
                    title=assignment_title,
                    course_id=selected_course_id if selected_course_id > 0 else None,
                    due_date=due_date.isoformat(),
                    due_time=due_time.strftime("%H:%M"),
                    description=description,
                    priority=priority
                )
                st.success(f"✅ Devoir '{assignment_title}' ajouté!")
                st.rerun()
        
        # Filtres
        subheader_with_icon('fa-clipboard-list', 'Mes Devoirs')
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.selectbox("Filtrer par statut", ["Tous"] + ASSIGNMENT_STATUS, key="filter_assign_status")
        with col2:
            filter_priority = st.selectbox("Filtrer par priorité", ["Toutes", "Urgent", "Important", "Normal", "Faible"], key="filter_assign_priority")
        with col3:
            view_mode = st.radio("Vue", ["Liste", "Kanban"], horizontal=True, key="assign_view")
        
        all_assignments = db.get_all_assignments()
        
        # Filtrage
        assignments = all_assignments.copy()
        if filter_status != "Tous":
            assignments = [a for a in assignments if a.get('status') == filter_status]
        
        if filter_priority != "Toutes":
            priority_map = {"Urgent": 1, "Important": 2, "Normal": 3, "Faible": 4}
            target_priority = priority_map.get(filter_priority)
            if target_priority:
                assignments = [a for a in assignments if a.get('priority') == target_priority]
        
        # Trier par date limite
        assignments.sort(key=lambda x: x.get('due_date', '9999-12-31'))
        
        if view_mode == "Kanban":
            # Vue Kanban
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.subheader("⏳ En Attente")
                pending = [a for a in assignments if a.get('status') == 'pending']
                for assignment in pending:
                    priority = assignment.get('priority', 3)
                    with st.container():
                        st.markdown(f"**{PRIORITIES[priority]} {assignment.get('title', '')}**")
                        st.caption(f"📅 {assignment.get('due_date', 'N/A')}")
                        if assignment.get('description'):
                            st.caption(assignment.get('description', '')[:50] + "...")
                        new_status = st.selectbox("", ASSIGNMENT_STATUS, 
                                                 index=0, key=f"kanban_status_{assignment.get('id')}")
                        if new_status != 'pending':
                            db.update_assignment_status(assignment.get('id'), new_status)
                            st.rerun()
                        if st.button("🗑️", key=f"kanban_del_{assignment.get('id')}"):
                            db.delete_assignment(assignment.get('id'))
                            st.rerun()
            
            with col2:
                st.subheader("🔄 En Cours")
                in_progress = [a for a in assignments if a.get('status') == 'in_progress']
                for assignment in in_progress:
                    priority = assignment.get('priority', 3)
                    with st.container():
                        st.markdown(f"**{PRIORITIES[priority]} {assignment.get('title', '')}**")
                        st.caption(f"📅 {assignment.get('due_date', 'N/A')}")
                        if assignment.get('description'):
                            st.caption(assignment.get('description', '')[:50] + "...")
                        new_status = st.selectbox("", ASSIGNMENT_STATUS, 
                                                 index=1, key=f"kanban_status_{assignment.get('id')}")
                        if new_status != 'in_progress':
                            db.update_assignment_status(assignment.get('id'), new_status)
                            st.rerun()
                        if st.button("🗑️", key=f"kanban_del_{assignment.get('id')}"):
                            db.delete_assignment(assignment.get('id'))
                            st.rerun()
            
            with col3:
                st.subheader("✅ Terminé")
                completed = [a for a in assignments if a.get('status') == 'completed']
                for assignment in completed:
                    priority = assignment.get('priority', 3)
                    with st.container():
                        st.markdown(f"**{PRIORITIES[priority]} {assignment.get('title', '')}**")
                        st.caption(f"📅 {assignment.get('due_date', 'N/A')}")
                        if assignment.get('description'):
                            st.caption(assignment.get('description', '')[:50] + "...")
                        new_status = st.selectbox("", ASSIGNMENT_STATUS, 
                                                 index=2, key=f"kanban_status_{assignment.get('id')}")
                        if new_status != 'completed':
                            db.update_assignment_status(assignment.get('id'), new_status)
                            st.rerun()
                        if st.button("🗑️", key=f"kanban_del_{assignment.get('id')}"):
                            db.delete_assignment(assignment.get('id'))
                            st.rerun()
            
            with col4:
                st.subheader("❌ Annulé")
                cancelled = [a for a in assignments if a.get('status') == 'cancelled']
                for assignment in cancelled:
                    priority = assignment.get('priority', 3)
                    with st.container():
                        st.markdown(f"**{PRIORITIES[priority]} {assignment.get('title', '')}**")
                        st.caption(f"📅 {assignment.get('due_date', 'N/A')}")
                        if assignment.get('description'):
                            st.caption(assignment.get('description', '')[:50] + "...")
                        new_status = st.selectbox("", ASSIGNMENT_STATUS, 
                                                 index=3, key=f"kanban_status_{assignment.get('id')}")
                        if new_status != 'cancelled':
                            db.update_assignment_status(assignment.get('id'), new_status)
                            st.rerun()
                        if st.button("🗑️", key=f"kanban_del_{assignment.get('id')}"):
                            db.delete_assignment(assignment.get('id'))
                            st.rerun()
        else:
            # Vue Liste
            if assignments:
                for assignment in assignments:
                    status = assignment.get('status', 'pending')
                    priority = assignment.get('priority', 3)
                    with st.expander(f"{PRIORITIES[priority]} {assignment.get('title', '')} - {status}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Date limite:** {assignment.get('due_date', '')} à {assignment.get('due_time', '')}")
                            if assignment.get('description'):
                                st.write(f"**Description:** {assignment.get('description', '')}")
                            # Afficher le cours associé
                            if assignment.get('course_id'):
                                course = next((c for c in db.get_all_courses() if c.get('id') == assignment.get('course_id')), None)
                                if course:
                                    st.write(f"**Cours:** {course.get('name', '')}")
                        with col2:
                            new_status = st.selectbox("Statut", ASSIGNMENT_STATUS, 
                                                     index=ASSIGNMENT_STATUS.index(status) if status in ASSIGNMENT_STATUS else 0,
                                                     key=f"status_{assignment.get('id')}")
                            if new_status != status:
                                db.update_assignment_status(assignment.get('id'), new_status)
                                st.rerun()
                        
                        col3, col4 = st.columns(2)
                        with col3:
                            if st.button("✏️ Modifier", key=f"edit_assign_{assignment.get('id')}"):
                                st.session_state[f"editing_assign_{assignment.get('id')}"] = True
                        with col4:
                            if st.button("🗑️ Supprimer", key=f"del_assign_{assignment.get('id')}"):
                                db.delete_assignment(assignment.get('id'))
                                st.rerun()
            else:
                st.info("Aucun devoir trouvé avec ces filtres")
    
    with tab4:
        subheader_with_icon('fa-bowl-food', 'Rappel Tupperware')
        st.write("Les rappels Tupperware sont automatiquement envoyés la veille des jours d'école.")
        
        # Vérifier les cours de demain
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_weekday = tomorrow.weekday()
        courses_tomorrow = db.get_courses_by_day(tomorrow_weekday)
        
        if courses_tomorrow:
            st.info(f"📚 Tu as {len(courses_tomorrow)} cours demain ({WEEKDAYS[tomorrow_weekday]})")
            for course in courses_tomorrow:
                st.write(f"- {course.get('name', '')} à {course.get('start_time', '')}")
            
            if st.button("🔔 Envoyer Rappel Tupperware Maintenant"):
                result = send_tupperware_reminder(tomorrow)
                if result.get('email') or result.get('telegram'):
                    st.success("Rappel Tupperware envoyé!")
                else:
                    st.warning("Notifications non configurées. Voir Configuration.")
        else:
            st.info("Pas de cours demain ! 🎉")

# ==================== PAGE SECOND CERVEAU ====================
elif current_page == "Second Cerveau":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-brain', 'normal')}
            Second Cerveau - Gestion de Connaissances
        </h2>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs([
        "📝 Notes",
        "🔗 Liens",
        "💡 Connaissances"
    ])
    
    with tab1:
        subheader_with_icon('fa-file-lines', 'Mes Notes')
        
        # Ajouter une note
        with st.expander("➕ Créer une Note", expanded=False):
            note_title = st.text_input("Titre", key="note_title")
            note_content = st.text_area("Contenu", height=200, key="note_content")
            note_tags = st.text_input("Tags (séparés par des virgules)", key="note_tags", 
                                     placeholder="Ex: python, streamlit, projet")
            note_category = st.selectbox("Catégorie", SECOND_BRAIN_CATEGORIES, key="note_category")
            
            if st.button("➕ Créer la note", key="add_note_btn"):
                note_id = db.add_note(
                    title=note_title,
                    content=note_content,
                    tags=note_tags,
                    category=note_category
                )
                st.success(f"✅ Note '{note_title}' créée!")
                st.rerun()
        
        # Recherche et filtres
        search_query = st.text_input("🔍 Rechercher dans les notes", key="search_notes", 
                                     placeholder="Rechercher par titre, contenu, tags...")
        
        col1, col2 = st.columns(2)
        with col1:
            filter_category = st.selectbox("Filtrer par catégorie", ["Toutes"] + SECOND_BRAIN_CATEGORIES, key="filter_cat")
        with col2:
            filter_tag = st.text_input("Filtrer par tag", key="filter_tag")
        
        # Liste des notes
        if search_query:
            notes = db.search_notes(search_query)
        else:
            notes = db.get_all_notes(
                category=filter_category if filter_category != "Toutes" else None,
                tag=filter_tag if filter_tag else None
            )
        
        if notes:
            for note in notes:
                with st.expander(f"📝 {note.get('title', '')} - {note.get('category', '')}"):
                    st.write(note.get('content', ''))
                    if note.get('tags'):
                        tags_list = note.get('tags', '').split(',')
                        st.write("**Tags:** " + ", ".join([f"#{tag.strip()}" for tag in tags_list]))
                    st.write(f"**Créé:** {note.get('created_at', '')}")
                    st.write(f"**Modifié:** {note.get('updated_at', '')}")
                    
                    if st.button("✏️ Modifier", key=f"edit_note_{note.get('id')}"):
                        st.session_state[f"editing_note_{note.get('id')}"] = True
                    
                    if st.button("🗑️ Supprimer", key=f"del_note_{note.get('id')}"):
                        db.delete_note(note.get('id'))
                        st.rerun()
        else:
            st.info("Aucune note")
    
    with tab2:
        subheader_with_icon('fa-link', 'Mes Liens et Ressources')
        
        # Ajouter un lien
        with st.expander("➕ Ajouter un Lien", expanded=False):
            link_title = st.text_input("Titre", key="link_title")
            link_url = st.text_input("URL", key="link_url")
            link_description = st.text_area("Description", key="link_desc")
            link_tags = st.text_input("Tags", key="link_tags")
            link_category = st.selectbox("Catégorie", SECOND_BRAIN_CATEGORIES, key="link_category")
            
            if st.button("➕ Ajouter le lien", key="add_link_btn"):
                link_id = db.add_link(
                    title=link_title,
                    url=link_url,
                    description=link_description,
                    tags=link_tags,
                    category=link_category
                )
                st.success(f"✅ Lien '{link_title}' ajouté!")
                st.rerun()
        
        # Liste des liens
        links = db.get_all_links()
        if links:
            for link in links:
                with st.expander(f"🔗 {link.get('title', '')}"):
                    st.write(f"**URL:** [{link.get('url', '')}]({link.get('url', '')})")
                    if link.get('description'):
                        st.write(f"**Description:** {link.get('description', '')}")
                    if link.get('tags'):
                        st.write(f"**Tags:** {link.get('tags', '')}")
                    st.write(f"**Catégorie:** {link.get('category', '')}")
                    
                    if st.button("🗑️ Supprimer", key=f"del_link_{link.get('id')}"):
                        db.delete_link(link.get('id'))
                        st.rerun()
        else:
            st.info("Aucun lien enregistré")
    
    with tab3:
        subheader_with_icon('fa-lightbulb', 'Éléments de Connaissance')
        
        # Ajouter un élément
        with st.expander("➕ Ajouter un Élément", expanded=False):
            item_title = st.text_input("Titre", key="item_title")
            item_content = st.text_area("Contenu", height=200, key="item_content")
            item_type = st.selectbox("Type", KNOWLEDGE_TYPES, key="item_type")
            item_tags = st.text_input("Tags", key="item_tags")
            related_items = st.text_input("Éléments liés (IDs séparés par virgules)", key="related_items")
            
            if st.button("➕ Ajouter l'élément", key="add_item_btn"):
                item_id = db.add_knowledge_item(
                    title=item_title,
                    content=item_content,
                    type=item_type,
                    tags=item_tags,
                    related_items=related_items
                )
                st.success(f"✅ Élément '{item_title}' ajouté!")
                st.rerun()
        
        # Liste des éléments
        items = db.get_all_knowledge_items()
        if items:
            for item in items:
                with st.expander(f"💡 {item.get('title', '')} - {item.get('type', '')}"):
                    st.write(item.get('content', ''))
                    if item.get('tags'):
                        st.write(f"**Tags:** {item.get('tags', '')}")
                    if item.get('related_items'):
                        st.write(f"**Lié à:** {item.get('related_items', '')}")
                    st.write(f"**Créé:** {item.get('created_at', '')}")
                    
                    if st.button("🗑️ Supprimer", key=f"del_item_{item.get('id')}"):
                        db.delete_knowledge_item(item.get('id'))
                        st.rerun()
        else:
            st.info("Aucun élément de connaissance")

# ==================== PAGE CONFIGURATION ====================
elif current_page == "Configuration":
    st.markdown(f"""
        <h2 style="display: flex; align-items: center; gap: 0.5rem;">
            {get_icon_html('fa-gear', 'normal')}
            Configuration des Notifications
        </h2>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs([
        "📧 Email",
        "💬 Telegram",
        "📜 Historique"
    ])
    
    with tab1:
        st.subheader("Configuration Email")
        st.info("Configurez vos notifications par email. Les variables d'environnement sont utilisées.")
        
        st.write("**Variables d'environnement à configurer:**")
        st.code("""
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=votre_email@gmail.com
EMAIL_PASSWORD=votre_mot_de_passe_app
        """)
        
        st.write("**Pour Gmail:**")
        st.write("1. Activez l'authentification à 2 facteurs")
        st.write("2. Générez un mot de passe d'application")
        st.write("3. Utilisez ce mot de passe dans EMAIL_PASSWORD")
        
        # Test d'envoi
        if st.button("📧 Tester l'envoi d'email"):
            service = get_notification_service()
            result = service.send_notification(
                message="Ceci est un test de notification email.",
                subject="Test Notification",
                use_email=True,
                use_telegram=False
            )
            if result.get('email'):
                st.success("Email envoyé avec succès!")
                # Enregistrer dans l'historique
                db.add_notification_history(
                    notification_type="test",
                    recipient=service.email_config.get('sender_email', ''),
                    subject="Test Notification",
                    message="Ceci est un test de notification email.",
                    method="email",
                    status="sent"
                )
            else:
                st.error("Erreur lors de l'envoi. Vérifiez votre configuration.")
                db.add_notification_history(
                    notification_type="test",
                    subject="Test Notification",
                    message="Ceci est un test de notification email.",
                    method="email",
                    status="failed"
                )
    
    with tab2:
        st.subheader("Configuration Telegram")
        st.info("Configurez vos notifications Telegram.")
        
        st.write("**Comment créer un bot Telegram:**")
        st.write("1. Ouvrez Telegram et cherchez @BotFather")
        st.write("2. Envoyez /newbot et suivez les instructions")
        st.write("3. Copiez le token du bot")
        st.write("4. Pour obtenir votre chat_id, envoyez un message à votre bot puis visitez:")
        st.write("   https://api.telegram.org/bot<VOTRE_TOKEN>/getUpdates")
        
        st.write("**Variables d'environnement à configurer:**")
        st.code("""
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=votre_token_bot
TELEGRAM_CHAT_ID=votre_chat_id
        """)
        
        # Test d'envoi
        if st.button("💬 Tester l'envoi Telegram"):
            service = get_notification_service()
            result = service.send_notification(
                message="Ceci est un test de notification Telegram.",
                subject="Test Notification",
                use_email=False,
                use_telegram=True
            )
            if result.get('telegram'):
                st.success("Message Telegram envoyé avec succès!")
                db.add_notification_history(
                    notification_type="test",
                    recipient=service.telegram_config.get('chat_id', ''),
                    subject="Test Notification",
                    message="Ceci est un test de notification Telegram.",
                    method="telegram",
                    status="sent"
                )
            else:
                st.error("Erreur lors de l'envoi. Vérifiez votre configuration.")
                db.add_notification_history(
                    notification_type="test",
                    subject="Test Notification",
                    message="Ceci est un test de notification Telegram.",
                    method="telegram",
                    status="failed"
                )
    
    with tab3:
        st.subheader("📜 Historique des Notifications")
        history = db.get_notification_history(limit=50)
        
        if history:
            history_df = pd.DataFrame(history)
            history_df['sent_at'] = pd.to_datetime(history_df['sent_at'])
            history_df = history_df.sort_values('sent_at', ascending=False)
            
            st.dataframe(
                history_df[['notification_type', 'method', 'status', 'sent_at', 'subject']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Aucune notification envoyée pour le moment")

# Footer
st.markdown("---")
st.markdown(f"💪 **Objectif:** {DEFAULT_SPORT_SESSIONS_PER_DAY} séances de sport par jour!")
