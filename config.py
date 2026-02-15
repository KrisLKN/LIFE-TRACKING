"""
Configuration et constantes de l'application
"""

# Types d'événements
EVENT_TYPES = {
    'SPORT': '🏋️ Sport (Salle)',
    'WORK': '💼 Travail',
    'MEAL': '🍽️ Repas',
    'SLEEP': '😴 Sommeil',
    'STUDY': '📚 Étude',
    'LEISURE': '🎮 Loisir',
    'SOCIAL': '👥 Social',
    'WEIGHT': '⚖️ Poids',
    'HYDRATION': '💧 Hydratation',
    'OTHER': 'Autre'
}

# Types de séances de sport
SPORT_SESSION_TYPES = [
    'Haut du corps',
    'Bas du corps',
    'Full body',
    'Cardio',
    'HIIT',
    'Yoga',
    'Étirement',
    'Autre'
]

# Types d'activités cardio
CARDIO_TYPES = [
    'Course à pied',
    'Vélo',
    'Natation',
    'Rameur',
    'Elliptique',
    'Escalier',
    'Marche',
    'Autre'
]

# Types d'objectifs
OBJECTIVE_TYPES = [
    'Sport - Séances par semaine',
    'Sport - Poids soulevé',
    'Sport - Calories brûlées',
    'Nutrition - Calories quotidiennes',
    'Nutrition - Protéines quotidiennes',
    'Poids corporel',
    'Hydratation quotidienne',
    'Sommeil - Heures par nuit',
    'Autre'
]

# Fréquences d'objectifs
OBJECTIVE_FREQUENCIES = [
    'Quotidien',
    'Hebdomadaire',
    'Mensuel',
    'Unique'
]

# Statuts d'objectifs
OBJECTIVE_STATUS = {
    'ACTIVE': 'active',
    'COMPLETED': 'completed',
    'CANCELLED': 'cancelled'
}

# Types de rappels
REMINDER_TYPES = [
    'Sport',
    'Repas',
    'Hydratation',
    'Poids',
    'Sommeil',
    'Autre'
]

# Fréquences de rappels
REMINDER_FREQUENCIES = [
    'Quotidien',
    'Hebdomadaire',
    'Personnalisé'
]

# Objectif par défaut de séances de sport par jour
DEFAULT_SPORT_SESSIONS_PER_DAY = 5

# Configuration de l'export
EXPORT_FORMATS = ['CSV', 'Excel', 'PDF']

# Configuration des graphiques
CHART_COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ffbb33'
}

# Jours de la semaine
WEEKDAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

# Catégories Second Cerveau
SECOND_BRAIN_CATEGORIES = [
    'Idées',
    'Projets',
    'Références',
    'Apprentissage',
    'Réflexions',
    'Citations',
    'Autre'
]

# Types d'éléments de connaissance
KNOWLEDGE_TYPES = [
    'Concept',
    'Méthode',
    'Ressource',
    'Personne',
    'Lieu',
    'Événement',
    'Autre'
]

# Statuts des devoirs
ASSIGNMENT_STATUS = [
    'pending',
    'in_progress',
    'completed',
    'cancelled'
]

# Priorités
PRIORITIES = {
    1: '🔴 Urgent',
    2: '🟠 Important',
    3: '🟡 Normal',
    4: '🟢 Faible'
}

# Mapping des emojis vers les icônes Font Awesome
ICON_MAPPING = {
    '🏠': 'fa-home',
    '➕': 'fa-plus',
    '📊': 'fa-chart-line',
    '📈': 'fa-chart-bar',
    '🎯': 'fa-bullseye',
    '🏫': 'fa-school',
    '🧠': 'fa-brain',
    '🗓️': 'fa-calendar',
    '📤': 'fa-download',
    '🔔': 'fa-bell',
    '⚙️': 'fa-gear',
    '🏋️': 'fa-dumbbell',
    '🍽️': 'fa-utensils',
    '😴': 'fa-moon',
    '💧': 'fa-droplet',
    '⚖️': 'fa-weight-scale',
    '💼': 'fa-briefcase',
    '📚': 'fa-book',
    '🎮': 'fa-gamepad',
    '👥': 'fa-users',
    '📝': 'fa-file-lines',
    '🔗': 'fa-link',
    '💡': 'fa-lightbulb',
    '📖': 'fa-book-open',
    '✅': 'fa-check',
    '❌': 'fa-xmark',
    '🗑️': 'fa-trash',
    '✏️': 'fa-pencil',
    '📧': 'fa-envelope',
    '💬': 'fa-comment',
    '🔴': 'fa-circle',
    '🟠': 'fa-circle',
    '🟡': 'fa-circle',
    '🟢': 'fa-circle',
    '🍱': 'fa-bowl-food',
    '📋': 'fa-clipboard-list',
    '⏰': 'fa-clock',
    '📅': 'fa-calendar-days',
}

# Types d'événements avec icônes Font Awesome
EVENT_TYPES_WITH_ICONS = {
    'SPORT': ('fa-dumbbell', 'Sport (Salle)'),
    'WORK': ('fa-briefcase', 'Travail'),
    'MEAL': ('fa-utensils', 'Repas'),
    'SLEEP': ('fa-moon', 'Sommeil'),
    'STUDY': ('fa-book', 'Étude'),
    'LEISURE': ('fa-gamepad', 'Loisir'),
    'SOCIAL': ('fa-users', 'Social'),
    'WEIGHT': ('fa-weight-scale', 'Poids'),
    'HYDRATION': ('fa-droplet', 'Hydratation'),
    'OTHER': ('fa-circle', 'Autre')
}