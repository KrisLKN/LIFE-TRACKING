"""
Module de gestion du thème (mode clair/nuit)
et utilitaires pour les icônes Font Awesome
"""
import streamlit as st
from typing import Optional

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

def get_icon_html(icon_name: str, size: str = "normal", color: Optional[str] = None) -> str:
    """
    Génère le HTML pour une icône Font Awesome
    
    Args:
        icon_name: Nom de l'icône (ex: 'fa-home')
        size: Taille ('small', 'normal', 'large')
        color: Couleur personnalisée (optionnel)
    
    Returns:
        HTML de l'icône
    """
    size_class = {
        'small': 'fa-icon-small',
        'normal': 'fa-icon',
        'large': 'fa-icon-large'
    }.get(size, 'fa-icon')
    
    color_style = f' style="color: {color};"' if color else ''
    return f'<i class="fa-solid {icon_name} {size_class}"{color_style}></i>'

def emoji_to_icon(emoji: str, size: str = "normal") -> str:
    """
    Convertit un emoji en icône Font Awesome
    
    Args:
        emoji: Emoji à convertir
        size: Taille de l'icône
    
    Returns:
        HTML de l'icône ou l'emoji original si non trouvé
    """
    icon_name = ICON_MAPPING.get(emoji)
    if icon_name:
        return get_icon_html(icon_name, size)
    return emoji

def init_theme():
    """
    Initialise le système de thème avec détection automatique
    """
    if 'dark_mode' not in st.session_state:
        # Détection automatique via JavaScript (sera injecté dans app.py)
        st.session_state.dark_mode = False
    
    if 'theme_initialized' not in st.session_state:
        st.session_state.theme_initialized = True

def toggle_dark_mode():
    """
    Bascule entre mode clair et mode nuit
    """
    if 'dark_mode' in st.session_state:
        st.session_state.dark_mode = not st.session_state.dark_mode
    else:
        st.session_state.dark_mode = True

def is_dark_mode() -> bool:
    """
    Retourne True si le mode nuit est activé
    """
    return st.session_state.get('dark_mode', False)

def get_theme_css() -> str:
    """
    Retourne le CSS pour appliquer le thème
    """
    theme = "dark" if is_dark_mode() else "light"
    return f"""
    <style>
        :root {{
            color-scheme: {theme};
        }}
        [data-theme="{theme}"] {{
            display: block;
        }}
    </style>
    <script>
        // Appliquer le thème au document
        document.documentElement.setAttribute('data-theme', '{theme}');
        
        // Détection automatique du mode système
        if (!localStorage.getItem('darkMode')) {{
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        }}
    </script>
    """

def inject_font_awesome() -> str:
    """
    Injecte Font Awesome CDN dans la page avec fallback
    """
    return """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" 
          integrity="sha512-iecdLmaskl7CVkqkXNQ/ZH/XLlvWZOJyj7Yy7tcenmpD1ypASozpmT/E0iPtmFIB46ZmdtAc9eNBvH0H/ZpiBw==" 
          crossorigin="anonymous" 
          referrerpolicy="no-referrer" />
    <link rel="preconnect" href="https://cdnjs.cloudflare.com">
    <script>
        // Vérifier si Font Awesome est chargé
        window.addEventListener('load', function() {
            if (!document.querySelector('link[href*="font-awesome"]')) {
                console.warn('Font Awesome non chargé, utilisation des emojis');
            }
        });
    </script>
    """

def inject_custom_css() -> str:
    """
    Injecte le CSS personnalisé
    """
    import os
    # Chemin relatif depuis le répertoire racine
    css_path = os.path.join(os.path.dirname(__file__), 'assets', 'style.css')
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        return f"<style>{css_content}</style>"
    except FileNotFoundError:
        # Si le fichier n'existe pas, retourner un CSS minimal
        return """
        <style>
            :root {
                --bg-primary: #FFFFFF;
                --text-primary: #000000;
            }
            [data-theme="dark"] {
                --bg-primary: #1E1E1E;
                --text-primary: #FFFFFF;
            }
        </style>
        """

def render_icon_text(icon_name: str, text: str, size: str = "normal") -> str:
    """
    Génère du HTML pour une icône avec du texte
    
    Args:
        icon_name: Nom de l'icône Font Awesome
        text: Texte à afficher
        size: Taille de l'icône
    
    Returns:
        HTML formaté
    """
    icon_html = get_icon_html(icon_name, size)
    return f'<span class="icon-text">{icon_html} {text}</span>'
