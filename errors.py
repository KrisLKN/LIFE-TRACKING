"""
Système de gestion d'erreurs amélioré avec exceptions personnalisées
et gestion centralisée des erreurs
"""
import logging
import traceback
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Codes d'erreur standardisés"""
    # Erreurs de base de données
    DB_CONNECTION_ERROR = "DB_001"
    DB_QUERY_ERROR = "DB_002"
    DB_INTEGRITY_ERROR = "DB_003"
    DB_NOT_FOUND = "DB_004"
    
    # Erreurs de validation
    VALIDATION_ERROR = "VAL_001"
    VALIDATION_FORMAT_ERROR = "VAL_002"
    VALIDATION_RANGE_ERROR = "VAL_003"
    
    # Erreurs métier
    BUSINESS_LOGIC_ERROR = "BIZ_001"
    DUPLICATE_ENTRY = "BIZ_002"
    INVALID_STATE = "BIZ_003"
    
    # Erreurs système
    SYSTEM_ERROR = "SYS_001"
    CONFIGURATION_ERROR = "SYS_002"
    PERMISSION_ERROR = "SYS_003"
    
    # Erreurs de notification
    NOTIFICATION_ERROR = "NOT_001"
    NOTIFICATION_CONFIG_ERROR = "NOT_002"


class AppException(Exception):
    """Exception de base pour toutes les exceptions de l'application"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = None,
        details: Dict[str, Any] = None,
        original_exception: Exception = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'exception en dictionnaire pour sérialisation"""
        return {
            'error_code': self.error_code.value if self.error_code else None,
            'message': self.message,
            'details': self.details,
            'type': self.__class__.__name__
        }
    
    def __str__(self):
        code_str = f"[{self.error_code.value}] " if self.error_code else ""
        return f"{code_str}{self.message}"


# ============================================================================
# EXCEPTIONS DE BASE DE DONNÉES
# ============================================================================

class DatabaseError(AppException):
    """Exception de base pour les erreurs de base de données"""
    def __init__(self, message: str, details: Dict[str, Any] = None, original_exception: Exception = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DB_QUERY_ERROR,
            details=details,
            original_exception=original_exception
        )


class DatabaseConnectionError(DatabaseError):
    """Erreur de connexion à la base de données"""
    def __init__(self, message: str = "Impossible de se connecter à la base de données", 
                 details: Dict[str, Any] = None, original_exception: Exception = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DB_CONNECTION_ERROR,
            details=details,
            original_exception=original_exception
        )


class DatabaseIntegrityError(DatabaseError):
    """Erreur d'intégrité de la base de données (contraintes, clés étrangères, etc.)"""
    def __init__(self, message: str = "Erreur d'intégrité de la base de données",
                 details: Dict[str, Any] = None, original_exception: Exception = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DB_INTEGRITY_ERROR,
            details=details,
            original_exception=original_exception
        )


class DatabaseNotFoundError(DatabaseError):
    """Ressource non trouvée dans la base de données"""
    def __init__(self, resource_type: str, resource_id: Any = None,
                 details: Dict[str, Any] = None):
        message = f"{resource_type} non trouvé"
        if resource_id is not None:
            message += f" (ID: {resource_id})"
        details = details or {}
        details.update({'resource_type': resource_type, 'resource_id': resource_id})
        super().__init__(
            message=message,
            error_code=ErrorCode.DB_NOT_FOUND,
            details=details
        )


# ============================================================================
# EXCEPTIONS DE VALIDATION
# ============================================================================

class ValidationError(AppException):
    """Exception pour les erreurs de validation"""
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        details = details or {}
        if field:
            details['field'] = field
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=details
        )
        self.field = field


class ValidationFormatError(ValidationError):
    """Erreur de format de validation"""
    def __init__(self, field: str, expected_format: str, actual_value: Any = None):
        message = f"Format invalide pour le champ '{field}'. Format attendu: {expected_format}"
        if actual_value is not None:
            message += f" (valeur reçue: {actual_value})"
        super().__init__(
            message=message,
            field=field,
            details={'expected_format': expected_format, 'actual_value': actual_value}
        )


class ValidationRangeError(ValidationError):
    """Erreur de plage de validation"""
    def __init__(self, field: str, min_value: Any = None, max_value: Any = None, actual_value: Any = None):
        range_parts = []
        if min_value is not None:
            range_parts.append(f"minimum: {min_value}")
        if max_value is not None:
            range_parts.append(f"maximum: {max_value}")
        range_str = ", ".join(range_parts)
        
        message = f"Valeur hors plage pour le champ '{field}' ({range_str})"
        if actual_value is not None:
            message += f" (valeur reçue: {actual_value})"
        
        super().__init__(
            message=message,
            field=field,
            details={'min_value': min_value, 'max_value': max_value, 'actual_value': actual_value}
        )


# ============================================================================
# EXCEPTIONS MÉTIER
# ============================================================================

class BusinessLogicError(AppException):
    """Exception pour les erreurs de logique métier"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.BUSINESS_LOGIC_ERROR,
            details=details
        )


class DuplicateEntryError(BusinessLogicError):
    """Erreur de doublon"""
    def __init__(self, resource_type: str, duplicate_field: str = None, details: Dict[str, Any] = None):
        message = f"{resource_type} déjà existant"
        if duplicate_field:
            message += f" (champ dupliqué: {duplicate_field})"
        details = details or {}
        details.update({'resource_type': resource_type, 'duplicate_field': duplicate_field})
        super().__init__(
            message=message,
            error_code=ErrorCode.DUPLICATE_ENTRY,
            details=details
        )


class InvalidStateError(BusinessLogicError):
    """Erreur d'état invalide"""
    def __init__(self, resource_type: str, current_state: str, expected_states: list = None,
                 details: Dict[str, Any] = None):
        message = f"État invalide pour {resource_type} (état actuel: {current_state})"
        if expected_states:
            message += f" (états attendus: {', '.join(expected_states)})"
        details = details or {}
        details.update({
            'resource_type': resource_type,
            'current_state': current_state,
            'expected_states': expected_states
        })
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_STATE,
            details=details
        )


# ============================================================================
# EXCEPTIONS SYSTÈME
# ============================================================================

class SystemError(AppException):
    """Exception pour les erreurs système"""
    def __init__(self, message: str, details: Dict[str, Any] = None, original_exception: Exception = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.SYSTEM_ERROR,
            details=details,
            original_exception=original_exception
        )


class ConfigurationError(SystemError):
    """Erreur de configuration"""
    def __init__(self, config_key: str = None, message: str = None, details: Dict[str, Any] = None):
        if not message:
            message = "Erreur de configuration"
            if config_key:
                message += f" (clé: {config_key})"
        details = details or {}
        if config_key:
            details['config_key'] = config_key
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            details=details
        )


class PermissionError(AppException):
    """Erreur de permission"""
    def __init__(self, message: str = "Permission refusée", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.PERMISSION_ERROR,
            details=details
        )


# ============================================================================
# EXCEPTIONS DE NOTIFICATION
# ============================================================================

class NotificationError(AppException):
    """Exception pour les erreurs de notification"""
    def __init__(self, message: str, notification_type: str = None, details: Dict[str, Any] = None):
        details = details or {}
        if notification_type:
            details['notification_type'] = notification_type
        super().__init__(
            message=message,
            error_code=ErrorCode.NOTIFICATION_ERROR,
            details=details
        )


class NotificationConfigError(NotificationError):
    """Erreur de configuration de notification"""
    def __init__(self, notification_type: str, message: str = None, details: Dict[str, Any] = None):
        if not message:
            message = f"Configuration invalide pour les notifications {notification_type}"
        super().__init__(
            message=message,
            notification_type=notification_type,
            error_code=ErrorCode.NOTIFICATION_CONFIG_ERROR,
            details=details
        )


# ============================================================================
# GESTIONNAIRE D'ERREURS CENTRALISÉ
# ============================================================================

class ErrorHandler:
    """Gestionnaire centralisé des erreurs"""
    
    @staticmethod
    def handle_error(exception: Exception, context: str = None) -> Dict[str, Any]:
        """
        Gère une exception et retourne un dictionnaire d'erreur formaté
        
        Args:
            exception: Exception à gérer
            context: Contexte de l'erreur (nom de la fonction, etc.)
        
        Returns:
            Dictionnaire avec les informations d'erreur
        """
        # Logger l'erreur
        error_context = f" dans {context}" if context else ""
        logger.error(f"Erreur{error_context}: {exception}", exc_info=True)
        
        # Si c'est une exception personnalisée, utiliser sa méthode to_dict
        if isinstance(exception, AppException):
            error_dict = exception.to_dict()
        else:
            # Exception générique
            error_dict = {
                'error_code': ErrorCode.SYSTEM_ERROR.value,
                'message': str(exception),
                'details': {
                    'exception_type': exception.__class__.__name__,
                    'traceback': traceback.format_exc()
                },
                'type': 'SystemError'
            }
        
        # Ajouter le contexte si fourni
        if context:
            error_dict['context'] = context
        
        return error_dict
    
    @staticmethod
    def safe_execute(operation, error_message: str = "Erreur lors de l'opération", 
                    default_return=None, context: str = None):
        """
        Exécute une opération de manière sécurisée avec gestion d'erreurs
        
        Args:
            operation: Fonction à exécuter (callable)
            error_message: Message d'erreur personnalisé
            default_return: Valeur à retourner en cas d'erreur
            context: Contexte de l'opération
        
        Returns:
            Résultat de l'opération ou default_return en cas d'erreur
        """
        try:
            return operation()
        except AppException as e:
            # Exceptions personnalisées - les laisser remonter
            ErrorHandler.handle_error(e, context)
            raise
        except Exception as e:
            # Exceptions génériques - les convertir
            error_dict = ErrorHandler.handle_error(e, context)
            logger.error(f"{error_message}: {error_dict['message']}")
            if default_return is not None:
                return default_return
            raise SystemError(
                message=error_message,
                details=error_dict['details'],
                original_exception=e
            )
    
    @staticmethod
    def format_user_message(exception: Exception) -> str:
        """
        Formate un message d'erreur convivial pour l'utilisateur
        
        Args:
            exception: Exception à formater
        
        Returns:
            Message formaté pour l'utilisateur
        """
        if isinstance(exception, AppException):
            # Messages d'erreur personnalisés déjà conviviaux
            return exception.message
        elif isinstance(exception, ValueError):
            return f"Valeur invalide: {str(exception)}"
        elif isinstance(exception, KeyError):
            return f"Clé manquante: {str(exception)}"
        elif isinstance(exception, AttributeError):
            return f"Attribut manquant: {str(exception)}"
        else:
            # Message générique pour les erreurs système
            return "Une erreur inattendue s'est produite. Veuillez réessayer."


# ============================================================================
# DÉCORATEUR POUR GESTION D'ERREURS
# ============================================================================

def handle_errors(error_message: str = None, default_return=None):
    """
    Décorateur pour gérer automatiquement les erreurs
    
    Usage:
        @handle_errors("Erreur lors de l'ajout d'événement")
        def add_event(...):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            context = f"{func.__name__}"
            msg = error_message or f"Erreur dans {func.__name__}"
            return ErrorHandler.safe_execute(
                lambda: func(*args, **kwargs),
                error_message=msg,
                default_return=default_return,
                context=context
            )
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
