"""
Interface utilisateur améliorée avec plus d'options et interactions
- Composants réutilisables
- Interactions rapides
- Design moderne
- Gestion d'erreurs intégrée
"""
import streamlit as st
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
import time
from errors import ErrorHandler, ValidationError, DatabaseError
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# COMPOSANTS UI RAPIDES ET INTELLIGENTS
# ============================================================================

def quick_action_button(
    label: str,
    icon: str,
    action: Callable,
    success_message: str = "Action réussie!",
    error_message: str = "Erreur lors de l'action",
    args: tuple = (),
    kwargs: dict = None,
    button_type: str = "primary"
):
    """
    Bouton d'action rapide avec gestion d'erreurs automatique
    
    Args:
        label: Texte du bouton
        icon: Emoji ou icône
        action: Fonction à exécuter
        success_message: Message de succès
        error_message: Message d'erreur
        args: Arguments positionnels
        kwargs: Arguments nommés
        button_type: Type de bouton (primary, secondary, success, danger)
    """
    kwargs = kwargs or {}
    
    button_label = f"{icon} {label}"
    
    if button_type == "primary":
        clicked = st.button(button_label, type="primary", use_container_width=True)
    elif button_type == "danger":
        clicked = st.button(button_label, type="secondary", use_container_width=True)
    else:
        clicked = st.button(button_label, use_container_width=True)
    
    if clicked:
        try:
            with st.spinner("Traitement en cours..."):
                result = action(*args, **kwargs)
            
            st.success(f"✅ {success_message}")
            if result is not None:
                return result
        except ValidationError as e:
            st.error(f"❌ Erreur de validation: {e.message}")
            if e.field:
                st.info(f"Champ concerné: **{e.field}**")
        except DatabaseError as e:
            st.error(f"❌ Erreur de base de données: {e.message}")
            st.info("Vérifiez la connexion à la base de données")
        except Exception as e:
            error_msg = ErrorHandler.format_user_message(e)
            st.error(f"❌ {error_message}: {error_msg}")
            logger.error(f"Erreur dans quick_action_button: {e}", exc_info=True)
    
    return None


def smart_input(
    label: str,
    input_type: str = "text",
    default_value: Any = None,
    help_text: str = None,
    validation_func: Callable = None,
    required: bool = False,
    **kwargs
) -> Any:
    """
    Input intelligent avec validation automatique
    
    Args:
        label: Label du champ
        input_type: Type (text, number, date, time, textarea, select)
        default_value: Valeur par défaut
        help_text: Texte d'aide
        validation_func: Fonction de validation
        required: Champ obligatoire
        **kwargs: Arguments supplémentaires pour Streamlit
    """
    key = f"input_{label.replace(' ', '_').lower()}"
    
    # Ajouter * pour les champs obligatoires
    display_label = f"{label} {'*' if required else ''}"
    
    try:
        if input_type == "text":
            value = st.text_input(display_label, value=default_value, help=help_text, key=key, **kwargs)
        elif input_type == "number":
            value = st.number_input(display_label, value=default_value, help=help_text, key=key, **kwargs)
        elif input_type == "date":
            value = st.date_input(display_label, value=default_value, help=help_text, key=key, **kwargs)
        elif input_type == "time":
            value = st.time_input(display_label, value=default_value, help=help_text, key=key, **kwargs)
        elif input_type == "textarea":
            value = st.text_area(display_label, value=default_value, help=help_text, key=key, **kwargs)
        elif input_type == "select":
            options = kwargs.pop('options', [])
            value = st.selectbox(display_label, options=options, index=0 if default_value not in options else options.index(default_value), help=help_text, key=key, **kwargs)
        else:
            value = st.text_input(display_label, value=default_value, help=help_text, key=key, **kwargs)
        
        # Validation
        if required and (value is None or value == ""):
            st.warning(f"⚠️ Le champ '{label}' est obligatoire")
            return None
        
        if validation_func and value:
            try:
                validation_func(value)
            except Exception as e:
                st.error(f"❌ Validation échouée: {str(e)}")
                return None
        
        return value
    except Exception as e:
        st.error(f"❌ Erreur dans le champ '{label}': {ErrorHandler.format_user_message(e)}")
        logger.error(f"Erreur dans smart_input: {e}", exc_info=True)
        return None


def enhanced_data_table(
    data: List[Dict],
    columns: Optional[List[str]] = None,
    searchable: bool = True,
    sortable: bool = True,
    filterable: bool = True,
    actions: Optional[Dict[str, Callable]] = None,
    key_prefix: str = "table"
):
    """
    Table de données améliorée avec recherche, tri et filtres
    
    Args:
        data: Liste de dictionnaires
        columns: Colonnes à afficher (None = toutes)
        searchable: Activer la recherche
        sortable: Activer le tri
        filterable: Activer les filtres
        actions: Actions disponibles ({"Modifier": func, "Supprimer": func})
        key_prefix: Préfixe pour les clés Streamlit
    """
    if not data:
        st.info("📭 Aucune donnée à afficher")
        return
    
    # Recherche
    filtered_data = data
    if searchable:
        search_term = st.text_input("🔍 Rechercher", key=f"{key_prefix}_search")
        if search_term:
            filtered_data = [
                row for row in data
                if any(search_term.lower() in str(val).lower() for val in row.values())
            ]
    
    # Filtres
    if filterable and filtered_data:
        col1, col2 = st.columns(2)
        with col1:
            filter_column = st.selectbox(
                "Filtrer par colonne",
                options=list(filtered_data[0].keys()) if filtered_data else [],
                key=f"{key_prefix}_filter_col"
            )
        with col2:
            if filter_column and filtered_data:
                unique_values = sorted(set(str(row.get(filter_column, '')) for row in filtered_data))
                filter_value = st.selectbox(
                    "Valeur",
                    options=["Tous"] + unique_values,
                    key=f"{key_prefix}_filter_val"
                )
                if filter_value != "Tous":
                    filtered_data = [row for row in filtered_data if str(row.get(filter_column, '')) == filter_value]
    
    # Affichage
    if not filtered_data:
        st.warning("🔍 Aucun résultat trouvé")
        return
    
    # Tri
    if sortable and filtered_data:
        sort_column = st.selectbox(
            "Trier par",
            options=list(filtered_data[0].keys()) if filtered_data else [],
            key=f"{key_prefix}_sort"
        )
        reverse = st.checkbox("Ordre décroissant", key=f"{key_prefix}_reverse")
        if sort_column:
            try:
                filtered_data = sorted(
                    filtered_data,
                    key=lambda x: str(x.get(sort_column, '')),
                    reverse=reverse
                )
            except Exception as e:
                logger.error(f"Erreur lors du tri: {e}")
    
    # Table
    st.write(f"**{len(filtered_data)} résultat(s)**")
    
    # Afficher les données
    for idx, row in enumerate(filtered_data):
        with st.expander(f"📋 {row.get('name', row.get('title', f'Item {idx+1}'))}", expanded=False):
            cols = st.columns(len(row) + (len(actions) if actions else 0))
            
            for col_idx, (key, value) in enumerate(row.items()):
                if columns is None or key in columns:
                    with cols[col_idx]:
                        st.write(f"**{key}:**")
                        st.write(value)
            
            # Actions
            if actions:
                st.divider()
                action_cols = st.columns(len(actions))
                for action_idx, (action_name, action_func) in enumerate(actions.items()):
                    with action_cols[action_idx]:
                        if st.button(f"⚡ {action_name}", key=f"{key_prefix}_action_{idx}_{action_name}"):
                            try:
                                action_func(row)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur: {ErrorHandler.format_user_message(e)}")


def quick_stats_cards(stats: Dict[str, Any], columns: int = 4):
    """
    Affiche des cartes de statistiques rapides
    
    Args:
        stats: Dictionnaire {nom: valeur}
        columns: Nombre de colonnes
    """
    cols = st.columns(columns)
    stat_items = list(stats.items())
    
    for idx, (name, value) in enumerate(stat_items):
        with cols[idx % columns]:
            st.metric(
                label=name,
                value=value,
                delta=None
            )


def smart_form(
    title: str,
    fields: List[Dict[str, Any]],
    submit_label: str = "Soumettre",
    on_submit: Callable = None,
    success_message: str = "Formulaire soumis avec succès!",
    key_prefix: str = "form"
):
    """
    Formulaire intelligent avec validation automatique
    
    Args:
        title: Titre du formulaire
        fields: Liste de champs [{"label": "...", "type": "...", "key": "...", ...}]
        submit_label: Label du bouton de soumission
        on_submit: Fonction appelée à la soumission
        success_message: Message de succès
        key_prefix: Préfixe pour les clés
    """
    st.subheader(title)
    
    with st.form(f"{key_prefix}_form"):
        form_data = {}
        
        for field in fields:
            field_key = field.get('key', field['label'].lower().replace(' ', '_'))
            full_key = f"{key_prefix}_{field_key}"
            
            field_type = field.get('type', 'text')
            label = field.get('label', field_key)
            default = field.get('default', None)
            required = field.get('required', False)
            help_text = field.get('help', None)
            validation = field.get('validation', None)
            
            value = smart_input(
                label=label,
                input_type=field_type,
                default_value=default,
                help_text=help_text,
                validation_func=validation,
                required=required,
                key=full_key,
                **{k: v for k, v in field.items() if k not in ['label', 'type', 'key', 'default', 'required', 'help', 'validation']}
            )
            
            form_data[field_key] = value
        
        submitted = st.form_submit_button(f"✅ {submit_label}", type="primary", use_container_width=True)
        
        if submitted:
            # Vérifier les champs obligatoires
            missing_fields = [
                field.get('label', field.get('key', ''))
                for field in fields
                if field.get('required', False) and form_data.get(field.get('key', field['label'].lower().replace(' ', '_'))) is None
            ]
            
            if missing_fields:
                st.error(f"❌ Champs obligatoires manquants: {', '.join(missing_fields)}")
                return None
            
            # Appeler la fonction de soumission
            if on_submit:
                try:
                    result = on_submit(form_data)
                    st.success(f"✅ {success_message}")
                    time.sleep(1)  # Petit délai pour voir le message
                    st.rerun()
                    return result
                except ValidationError as e:
                    st.error(f"❌ Erreur de validation: {e.message}")
                    if e.field:
                        st.info(f"Champ concerné: **{e.field}**")
                except DatabaseError as e:
                    st.error(f"❌ Erreur de base de données: {e.message}")
                except Exception as e:
                    st.error(f"❌ Erreur: {ErrorHandler.format_user_message(e)}")
                    logger.error(f"Erreur dans smart_form: {e}", exc_info=True)
            
            return form_data
    
    return None


def progress_tracker(steps: List[str], current_step: int = 0):
    """
    Affiche une barre de progression pour les étapes
    
    Args:
        steps: Liste des étapes
        current_step: Étape actuelle (0-indexed)
    """
    progress = (current_step + 1) / len(steps)
    st.progress(progress)
    
    cols = st.columns(len(steps))
    for idx, step in enumerate(steps):
        with cols[idx]:
            if idx <= current_step:
                st.success(f"✅ {step}")
            else:
                st.info(f"⏳ {step}")


def notification_banner(message: str, type: str = "info", dismissible: bool = True):
    """
    Affiche une bannière de notification
    
    Args:
        message: Message à afficher
        type: Type (info, success, warning, error)
        dismissible: Peut être fermée
    """
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    colors = {
        "info": "#2196F3",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336"
    }
    
    icon = icons.get(type, "ℹ️")
    color = colors.get(type, "#2196F3")
    
    st.markdown(
        f"""
        <div style="
            background-color: {color}20;
            border-left: 4px solid {color};
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 4px;
        ">
            <strong>{icon} {message}</strong>
        </div>
        """,
        unsafe_allow_html=True
    )


def quick_filters(
    filters: Dict[str, List[str]],
    key_prefix: str = "filters"
) -> Dict[str, str]:
    """
    Crée rapidement des filtres interactifs
    
    Args:
        filters: Dictionnaire {nom_filtre: [options]}
        key_prefix: Préfixe pour les clés
    
    Returns:
        Dictionnaire {nom_filtre: valeur_sélectionnée}
    """
    selected_filters = {}
    cols = st.columns(len(filters))
    
    for idx, (filter_name, options) in enumerate(filters.items()):
        with cols[idx]:
            selected = st.selectbox(
                filter_name,
                options=["Tous"] + options,
                key=f"{key_prefix}_{filter_name}"
            )
            if selected != "Tous":
                selected_filters[filter_name] = selected
    
    return selected_filters


def auto_refresh(interval_seconds: int = 30, key: str = "auto_refresh"):
    """
    Active le rafraîchissement automatique de la page
    
    Args:
        interval_seconds: Intervalle en secondes
        key: Clé pour le state
    """
    if st.checkbox("🔄 Rafraîchissement automatique", key=key):
        time.sleep(interval_seconds)
        st.rerun()


def error_boundary(func: Callable, error_message: str = "Une erreur s'est produite"):
    """
    Wrapper pour capturer toutes les erreurs d'une fonction
    
    Args:
        func: Fonction à exécuter
        error_message: Message d'erreur par défaut
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            st.error(f"❌ Erreur de validation: {e.message}")
            if e.field:
                st.info(f"Champ: **{e.field}**")
        except DatabaseError as e:
            st.error(f"❌ Erreur de base de données: {e.message}")
            st.info("💡 Vérifiez la connexion à la base de données")
        except Exception as e:
            error_dict = ErrorHandler.handle_error(e, context=func.__name__)
            st.error(f"❌ {error_message}")
            st.error(f"Détails: {ErrorHandler.format_user_message(e)}")
            
            # Afficher les détails techniques si en mode debug
            if st.session_state.get('debug_mode', False):
                with st.expander("🔍 Détails techniques"):
                    st.json(error_dict)
            
            logger.error(f"Erreur dans {func.__name__}: {e}", exc_info=True)
            return None
    
    return wrapper


def loading_spinner(message: str = "Chargement..."):
    """
    Contexte manager pour afficher un spinner de chargement
    
    Usage:
        with loading_spinner("Chargement des données"):
            data = load_data()
    """
    return st.spinner(message)


def success_toast(message: str, duration: float = 2.0):
    """
    Affiche un message de succès temporaire
    
    Args:
        message: Message à afficher
        duration: Durée d'affichage en secondes
    """
    st.success(f"✅ {message}")
    time.sleep(duration)


def error_toast(message: str, duration: float = 3.0):
    """
    Affiche un message d'erreur temporaire
    
    Args:
        message: Message à afficher
        duration: Durée d'affichage en secondes
    """
    st.error(f"❌ {message}")
    time.sleep(duration)
