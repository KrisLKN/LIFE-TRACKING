"""
Gestionnaire de configuration centralisée
- Chargement depuis fichiers (YAML/TOML/JSON)
- Variables d'environnement
- Validation de configuration
- Configuration par environnement (dev/prod)
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import tomllib
    TOML_AVAILABLE = True
except ImportError:
    try:
        import tomli as tomllib
        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False


@dataclass
class DatabaseConfig:
    """Configuration de la base de données"""
    db_file: str = "tracker.db"
    backup_file: str = "events_data.json"
    backup_interval_minutes: int = 5
    connection_timeout: float = 10.0
    enable_foreign_keys: bool = True


@dataclass
class SecurityConfig:
    """Configuration de sécurité"""
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    enable_audit_logging: bool = True
    audit_log_file: str = "audit.log"
    enable_encryption: bool = False
    encryption_key_file: Optional[str] = None


@dataclass
class CacheConfig:
    """Configuration du cache"""
    max_size: int = 1000
    default_ttl: int = 3600
    enable_cache: bool = True


@dataclass
class NotificationConfig:
    """Configuration des notifications"""
    email_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_sender: str = ""
    email_password: str = ""
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


@dataclass
class AppConfig:
    """Configuration complète de l'application"""
    database: DatabaseConfig
    security: SecurityConfig
    cache: CacheConfig
    notifications: NotificationConfig
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"


class ConfigManager:
    """
    Gestionnaire de configuration centralisé
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialise le gestionnaire de configuration
        
        Args:
            config_file: Chemin vers le fichier de configuration (optionnel)
        """
        self.config_file = config_file
        self.config: Optional[AppConfig] = None
        self._load_config()
    
    def _load_config(self):
        """Charge la configuration depuis les fichiers et variables d'environnement"""
        # Charger depuis le fichier si fourni
        file_config = {}
        if self.config_file and Path(self.config_file).exists():
            file_config = self._load_config_file(self.config_file)
        
        # Charger depuis les variables d'environnement (priorité plus élevée)
        env_config = self._load_from_env()
        
        # Fusionner les configurations (env > file > defaults)
        config_dict = self._merge_configs(file_config, env_config)
        
        # Créer l'objet de configuration
        self.config = self._create_config(config_dict)
        
        logger.info(f"Configuration chargée (environnement: {self.config.environment})")
    
    def _load_config_file(self, file_path: str) -> Dict[str, Any]:
        """Charge la configuration depuis un fichier"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        try:
            if suffix == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif suffix in ['.yaml', '.yml'] and YAML_AVAILABLE:
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            elif suffix == '.toml' and TOML_AVAILABLE:
                with open(path, 'rb') as f:
                    return tomllib.load(f)
            else:
                logger.warning(f"Format de fichier non supporté: {suffix}")
                return {}
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            return {}
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Charge la configuration depuis les variables d'environnement"""
        config = {}
        
        # Base de données
        if os.getenv('DB_FILE'):
            config.setdefault('database', {})['db_file'] = os.getenv('DB_FILE')
        if os.getenv('BACKUP_INTERVAL_MINUTES'):
            config.setdefault('database', {})['backup_interval_minutes'] = int(
                os.getenv('BACKUP_INTERVAL_MINUTES')
            )
        
        # Sécurité
        if os.getenv('RATE_LIMIT_REQUESTS'):
            config.setdefault('security', {})['rate_limit_requests'] = int(
                os.getenv('RATE_LIMIT_REQUESTS')
            )
        if os.getenv('ENABLE_AUDIT_LOGGING'):
            config.setdefault('security', {})['enable_audit_logging'] = (
                os.getenv('ENABLE_AUDIT_LOGGING').lower() == 'true'
            )
        
        # Notifications
        if os.getenv('EMAIL_ENABLED'):
            config.setdefault('notifications', {})['email_enabled'] = (
                os.getenv('EMAIL_ENABLED').lower() == 'true'
            )
        if os.getenv('EMAIL_SMTP_SERVER'):
            config.setdefault('notifications', {})['email_smtp_server'] = os.getenv('EMAIL_SMTP_SERVER')
        if os.getenv('EMAIL_SENDER'):
            config.setdefault('notifications', {})['email_sender'] = os.getenv('EMAIL_SENDER')
        if os.getenv('EMAIL_PASSWORD'):
            config.setdefault('notifications', {})['email_password'] = os.getenv('EMAIL_PASSWORD')
        
        if os.getenv('TELEGRAM_ENABLED'):
            config.setdefault('notifications', {})['telegram_enabled'] = (
                os.getenv('TELEGRAM_ENABLED').lower() == 'true'
            )
        if os.getenv('TELEGRAM_BOT_TOKEN'):
            config.setdefault('notifications', {})['telegram_bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN')
        if os.getenv('TELEGRAM_CHAT_ID'):
            config.setdefault('notifications', {})['telegram_chat_id'] = os.getenv('TELEGRAM_CHAT_ID')
        
        # Application
        if os.getenv('ENVIRONMENT'):
            config['environment'] = os.getenv('ENVIRONMENT')
        if os.getenv('DEBUG'):
            config['debug'] = os.getenv('DEBUG').lower() == 'true'
        if os.getenv('LOG_LEVEL'):
            config['log_level'] = os.getenv('LOG_LEVEL')
        
        return config
    
    def _merge_configs(self, file_config: Dict, env_config: Dict) -> Dict:
        """Fusionne les configurations (env > file)"""
        merged = file_config.copy()
        
        def deep_merge(base: Dict, override: Dict):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(merged, env_config)
        return merged
    
    def _create_config(self, config_dict: Dict) -> AppConfig:
        """Crée l'objet de configuration à partir du dictionnaire"""
        db_config = DatabaseConfig(**config_dict.get('database', {}))
        security_config = SecurityConfig(**config_dict.get('security', {}))
        cache_config = CacheConfig(**config_dict.get('cache', {}))
        notification_config = NotificationConfig(**config_dict.get('notifications', {}))
        
        return AppConfig(
            database=db_config,
            security=security_config,
            cache=cache_config,
            notifications=notification_config,
            environment=config_dict.get('environment', 'production'),
            debug=config_dict.get('debug', False),
            log_level=config_dict.get('log_level', 'INFO')
        )
    
    def get_config(self) -> AppConfig:
        """Retourne la configuration"""
        if self.config is None:
            raise RuntimeError("Configuration non chargée")
        return self.config
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Valide la configuration
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Vérifier les chemins de fichiers
        if not Path(self.config.database.db_file).parent.exists():
            errors.append(f"Répertoire de la base de données n'existe pas: {Path(self.config.database.db_file).parent}")
        
        # Vérifier les notifications
        if self.config.notifications.email_enabled:
            if not self.config.notifications.email_sender:
                errors.append("Email activé mais EMAIL_SENDER non configuré")
            if not self.config.notifications.email_password:
                errors.append("Email activé mais EMAIL_PASSWORD non configuré")
        
        if self.config.notifications.telegram_enabled:
            if not self.config.notifications.telegram_bot_token:
                errors.append("Telegram activé mais TELEGRAM_BOT_TOKEN non configuré")
            if not self.config.notifications.telegram_chat_id:
                errors.append("Telegram activé mais TELEGRAM_CHAT_ID non configuré")
        
        return len(errors) == 0, errors


# Instance globale
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """Retourne l'instance globale du gestionnaire de configuration"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager


def get_config() -> AppConfig:
    """Retourne la configuration actuelle"""
    return get_config_manager().get_config()
