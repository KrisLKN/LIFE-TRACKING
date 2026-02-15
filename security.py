"""
Système de sécurité avancé
- Rate limiting
- Audit logging
- Chiffrement des données sensibles
- Protection CSRF
- Validation renforcée
"""
import hashlib
import hmac
import time
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Callable
from collections import defaultdict
from functools import wraps
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """
    Rate limiter pour protéger contre les abus
    Limite le nombre de requêtes par période de temps
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialise le rate limiter
        
        Args:
            max_requests: Nombre maximum de requêtes
            window_seconds: Fenêtre de temps en secondes
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.lock = False  # Simple lock pour thread safety basique
    
    def is_allowed(self, identifier: str) -> tuple[bool, Optional[str]]:
        """
        Vérifie si une requête est autorisée
        
        Args:
            identifier: Identifiant unique (IP, user_id, etc.)
        
        Returns:
            (is_allowed, message)
        """
        now = time.time()
        
        # Nettoyer les anciennes requêtes
        cutoff = now - self.window_seconds
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]
        
        # Vérifier la limite
        if len(self.requests[identifier]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self.requests[identifier][0]))
            return False, f"Trop de requêtes. Réessayez dans {retry_after} secondes"
        
        # Enregistrer la requête
        self.requests[identifier].append(now)
        return True, None
    
    def reset(self, identifier: str):
        """Réinitialise le compteur pour un identifiant"""
        if identifier in self.requests:
            del self.requests[identifier]


# Instance globale
_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Décorateur pour limiter le taux de requêtes
    
    Usage:
        @rate_limit(max_requests=10, window_seconds=60)
        def my_function():
            ...
    """
    limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Utiliser l'IP ou un identifiant de session
            identifier = kwargs.get('user_id') or 'default'
            allowed, message = limiter.is_allowed(identifier)
            
            if not allowed:
                raise PermissionError(message)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """
    Système d'audit logging pour tracer toutes les actions importantes
    """
    
    def __init__(self, log_file: str = "audit.log"):
        """
        Initialise l'audit logger
        
        Args:
            log_file: Chemin du fichier de log
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_action(
        self,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        ip_address: Optional[str] = None
    ):
        """
        Enregistre une action dans l'audit log
        
        Args:
            action: Type d'action (CREATE, UPDATE, DELETE, READ, etc.)
            user_id: ID de l'utilisateur
            resource_type: Type de ressource (event, exam, etc.)
            resource_id: ID de la ressource
            details: Détails supplémentaires
            success: Si l'action a réussi
            ip_address: Adresse IP
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user_id': user_id or 'system',
            'resource_type': resource_type,
            'resource_id': str(resource_id) if resource_id else None,
            'success': success,
            'ip_address': ip_address,
            'details': details or {}
        }
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture de l'audit log: {e}")
    
    def get_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Récupère les logs d'audit avec filtres
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            action: Filtrer par action
            user_id: Filtrer par utilisateur
            limit: Nombre maximum de résultats
        
        Returns:
            Liste des logs d'audit
        """
        if not self.log_file.exists():
            return []
        
        logs = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Filtres
                        if action and log_entry.get('action') != action:
                            continue
                        if user_id and log_entry.get('user_id') != user_id:
                            continue
                        
                        log_time = datetime.fromisoformat(log_entry['timestamp'])
                        if start_date and log_time < start_date:
                            continue
                        if end_date and log_time > end_date:
                            continue
                        
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
            
            # Trier par timestamp décroissant et limiter
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            return logs[:limit]
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de l'audit log: {e}")
            return []


# Instance globale
_audit_logger = AuditLogger()


def audit_log(action: str, resource_type: Optional[str] = None):
    """
    Décorateur pour logger automatiquement les actions
    
    Usage:
        @audit_log(action="CREATE", resource_type="event")
        def add_event(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                _audit_logger.log_action(
                    action=action,
                    resource_type=resource_type,
                    resource_id=result if isinstance(result, (int, str)) else None,
                    success=True
                )
                return result
            except Exception as e:
                _audit_logger.log_action(
                    action=action,
                    resource_type=resource_type,
                    success=False,
                    details={'error': str(e)}
                )
                raise
        return wrapper
    return decorator


# ============================================================================
# CHIFFREMENT
# ============================================================================

class DataEncryption:
    """
    Système de chiffrement pour les données sensibles
    Utilise Fernet (symmetric encryption)
    """
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialise le système de chiffrement
        
        Args:
            key: Clé de chiffrement (générée automatiquement si None)
        """
        try:
            from cryptography.fernet import Fernet
            self.Fernet = Fernet
        except ImportError:
            logger.warning("cryptography non disponible, chiffrement désactivé")
            self.Fernet = None
            return
        
        if key is None:
            # Générer une clé (en production, stocker de manière sécurisée)
            key = Fernet.generate_key()
        
        self.cipher = Fernet(key)
        self.key = key
    
    def encrypt(self, data: str) -> str:
        """
        Chiffre une chaîne de caractères
        
        Args:
            data: Données à chiffrer
        
        Returns:
            Données chiffrées (base64)
        """
        if not self.Fernet:
            return data  # Pas de chiffrement si non disponible
        
        try:
            encrypted = self.cipher.encrypt(data.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement: {e}")
            return data
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Déchiffre une chaîne de caractères
        
        Args:
            encrypted_data: Données chiffrées
        
        Returns:
            Données déchiffrées
        """
        if not self.Fernet:
            return encrypted_data
        
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement: {e}")
            return encrypted_data


# ============================================================================
# PROTECTION CSRF
# ============================================================================

class CSRFProtection:
    """
    Protection CSRF (Cross-Site Request Forgery)
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialise la protection CSRF
        
        Args:
            secret_key: Clé secrète (générée automatiquement si None)
        """
        self.secret_key = secret_key or secrets.token_urlsafe(32)
    
    def generate_token(self, session_id: str) -> str:
        """
        Génère un token CSRF
        
        Args:
            session_id: ID de session
        
        Returns:
            Token CSRF
        """
        message = f"{session_id}:{time.time()}"
        token = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"{token}:{int(time.time())}"
    
    def validate_token(self, token: str, session_id: str, max_age_seconds: int = 3600) -> bool:
        """
        Valide un token CSRF
        
        Args:
            token: Token à valider
            session_id: ID de session
            max_age_seconds: Âge maximum du token en secondes
        
        Returns:
            True si le token est valide
        """
        try:
            token_part, timestamp_str = token.rsplit(':', 1)
            timestamp = int(timestamp_str)
            
            # Vérifier l'âge
            if time.time() - timestamp > max_age_seconds:
                return False
            
            # Vérifier le token
            expected_message = f"{session_id}:{timestamp}"
            expected_token = hmac.new(
                self.secret_key.encode('utf-8'),
                expected_message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(token_part, expected_token)
        except (ValueError, AttributeError):
            return False


# ============================================================================
# VALIDATION DE SÉCURITÉ RENFORCÉE
# ============================================================================

class SecurityValidator:
    """
    Validateur de sécurité pour détecter les tentatives d'attaque
    """
    
    @staticmethod
    def detect_sql_injection(input_str: str) -> bool:
        """
        Détecte les tentatives d'injection SQL basiques
        
        Args:
            input_str: Chaîne à vérifier
        
        Returns:
            True si suspect
        """
        sql_keywords = [
            'union', 'select', 'insert', 'update', 'delete',
            'drop', 'create', 'alter', 'exec', 'execute',
            'script', 'javascript', 'onerror', 'onload'
        ]
        
        input_lower = input_str.lower()
        for keyword in sql_keywords:
            if keyword in input_lower:
                # Vérifier si c'est dans un contexte suspect
                if any(pattern in input_lower for pattern in [
                    f"'{keyword}",
                    f'"{keyword}',
                    f"({keyword}",
                    f";{keyword}",
                    f"--{keyword}"
                ]):
                    return True
        return False
    
    @staticmethod
    def detect_xss(input_str: str) -> bool:
        """
        Détecte les tentatives XSS basiques
        
        Args:
            input_str: Chaîne à vérifier
        
        Returns:
            True si suspect
        """
        xss_patterns = [
            '<script', '</script>', 'javascript:', 'onerror=',
            'onload=', '<iframe', '<img', 'onclick=', 'onmouseover=',
            'eval(', 'document.cookie', 'window.location'
        ]
        
        input_lower = input_str.lower()
        return any(pattern in input_lower for pattern in xss_patterns)
    
    @staticmethod
    def detect_path_traversal(input_str: str) -> bool:
        """
        Détecte les tentatives de path traversal
        
        Args:
            input_str: Chaîne à vérifier
        
        Returns:
            True si suspect
        """
        traversal_patterns = ['../', '..\\', '/etc/', 'c:\\', '..%2f', '..%5c']
        return any(pattern in input_str.lower() for pattern in traversal_patterns)
    
    @staticmethod
    def validate_input(input_str: str, input_type: str = "text") -> tuple[bool, Optional[str]]:
        """
        Valide une entrée avec toutes les vérifications de sécurité
        
        Args:
            input_str: Chaîne à valider
            input_type: Type d'entrée (text, url, email, etc.)
        
        Returns:
            (is_valid, error_message)
        """
        if not input_str:
            return True, None
        
        # Détection SQL injection
        if SecurityValidator.detect_sql_injection(input_str):
            return False, "Entrée suspecte détectée (injection SQL possible)"
        
        # Détection XSS
        if SecurityValidator.detect_xss(input_str):
            return False, "Entrée suspecte détectée (XSS possible)"
        
        # Détection path traversal
        if SecurityValidator.detect_path_traversal(input_str):
            return False, "Entrée suspecte détectée (path traversal possible)"
        
        return True, None


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_client_ip() -> str:
    """Récupère l'IP du client (pour Streamlit)"""
    # Streamlit ne fournit pas directement l'IP, utiliser un identifiant de session
    import streamlit as st
    if hasattr(st, 'session_state'):
        return st.session_state.get('session_id', 'unknown')
    return 'unknown'


def secure_hash(data: str, salt: Optional[str] = None) -> str:
    """
    Crée un hash sécurisé d'une chaîne
    
    Args:
        data: Données à hasher
        salt: Sel optionnel
    
    Returns:
        Hash hexadécimal
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    hash_obj = hashlib.sha256()
    hash_obj.update((data + salt).encode('utf-8'))
    return f"{hash_obj.hexdigest()}:{salt}"


def verify_hash(data: str, hash_with_salt: str) -> bool:
    """
    Vérifie un hash
    
    Args:
        data: Données originales
        hash_with_salt: Hash avec sel (format: "hash:salt")
    
    Returns:
        True si le hash correspond
    """
    try:
        stored_hash, salt = hash_with_salt.rsplit(':', 1)
        computed_hash = secure_hash(data, salt)
        computed_hash_only, _ = computed_hash.rsplit(':', 1)
        return hmac.compare_digest(stored_hash, computed_hash_only)
    except (ValueError, AttributeError):
        return False
