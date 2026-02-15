"""
Système de monitoring et observabilité
- Métriques de performance
- Health checks
- Alertes
- Dashboard de monitoring
"""
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil non disponible, certaines métriques seront désactivées")


@dataclass
class Metric:
    """Métrique de performance"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags or {}
        }


class MetricsCollector:
    """
    Collecteur de métriques de performance
    """
    
    def __init__(self, max_metrics: int = 10000):
        """
        Initialise le collecteur de métriques
        
        Args:
            max_metrics: Nombre maximum de métriques à conserver
        """
        self.max_metrics = max_metrics
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics))
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
    
    def record(self, name: str, value: float, tags: Dict[str, str] = None):
        """
        Enregistre une métrique
        
        Args:
            name: Nom de la métrique
            value: Valeur
            tags: Tags optionnels
        """
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags
        )
        self.metrics[name].append(metric)
    
    def increment(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Incrémente un compteur"""
        key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        self.counters[key] += value
        self.record(name, self.counters[key], tags)
    
    def timer(self, name: str):
        """
        Retourne un contexte manager pour mesurer le temps
        
        Usage:
            with metrics.timer('db_query'):
                db.query(...)
        """
        return TimerContext(self, name)
    
    def get_metric_stats(self, name: str, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Retourne les statistiques d'une métrique
        
        Args:
            name: Nom de la métrique
            window_minutes: Fenêtre de temps en minutes
        
        Returns:
            Statistiques (min, max, avg, count)
        """
        if name not in self.metrics:
            return {'count': 0}
        
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_metrics = [
            m for m in self.metrics[name]
            if m.timestamp >= cutoff
        ]
        
        if not recent_metrics:
            return {'count': 0}
        
        values = [m.value for m in recent_metrics]
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1] if values else None
        }
    
    def get_all_stats(self, window_minutes: int = 60) -> Dict[str, Dict[str, Any]]:
        """Retourne les statistiques de toutes les métriques"""
        return {
            name: self.get_metric_stats(name, window_minutes)
            for name in self.metrics.keys()
        }


class TimerContext:
    """Contexte manager pour mesurer le temps d'exécution"""
    
    def __init__(self, collector: MetricsCollector, metric_name: str):
        self.collector = collector
        self.metric_name = metric_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.collector.record(f"{self.metric_name}_duration", duration)
        return False


class HealthChecker:
    """
    Vérificateur de santé de l'application
    """
    
    def __init__(self):
        self.checks: Dict[str, Callable[[], tuple[bool, str]]] = {}
    
    def register_check(self, name: str, check_func: Callable[[], tuple[bool, str]]):
        """
        Enregistre une vérification de santé
        
        Args:
            name: Nom de la vérification
            check_func: Fonction qui retourne (is_healthy, message)
        """
        self.checks[name] = check_func
    
    def check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Exécute toutes les vérifications
        
        Returns:
            Dictionnaire avec les résultats de chaque vérification
        """
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                is_healthy, message = check_func()
                results[name] = {
                    'healthy': is_healthy,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
                if not is_healthy:
                    overall_healthy = False
            except Exception as e:
                results[name] = {
                    'healthy': False,
                    'message': f"Erreur lors de la vérification: {e}",
                    'timestamp': datetime.now().isoformat()
                }
                overall_healthy = False
        
        results['_overall'] = {
            'healthy': overall_healthy,
            'timestamp': datetime.now().isoformat()
        }
        
        return results


class SystemMonitor:
    """
    Moniteur système (CPU, mémoire, disque)
    """
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Retourne les métriques système"""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil non disponible'}
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'percent': disk.percent
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques système: {e}")
            return {'error': str(e)}


# Instances globales
_metrics_collector = MetricsCollector()
_health_checker = HealthChecker()
_system_monitor = SystemMonitor()


def get_metrics_collector() -> MetricsCollector:
    """Retourne l'instance globale du collecteur de métriques"""
    return _metrics_collector


def get_health_checker() -> HealthChecker:
    """Retourne l'instance globale du vérificateur de santé"""
    return _health_checker


def get_system_monitor() -> SystemMonitor:
    """Retourne l'instance globale du moniteur système"""
    return _system_monitor


# Vérifications de santé par défaut
def check_database_health(db_instance) -> tuple[bool, str]:
    """Vérifie la santé de la base de données"""
    try:
        conn = db_instance.get_connection()
        conn.execute("SELECT 1")
        return True, "Base de données accessible"
    except Exception as e:
        return False, f"Erreur de base de données: {e}"


def check_disk_space(min_free_gb: float = 1.0) -> tuple[bool, str]:
    """Vérifie l'espace disque disponible"""
    if not PSUTIL_AVAILABLE:
        return True, "Vérification désactivée (psutil non disponible)"
    
    try:
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024**3)
        if free_gb < min_free_gb:
            return False, f"Espace disque faible: {free_gb:.2f} GB disponible"
        return True, f"Espace disque OK: {free_gb:.2f} GB disponible"
    except Exception as e:
        return False, f"Erreur lors de la vérification: {e}"


def check_memory_usage(max_percent: float = 90.0) -> tuple[bool, str]:
    """Vérifie l'utilisation de la mémoire"""
    if not PSUTIL_AVAILABLE:
        return True, "Vérification désactivée (psutil non disponible)"
    
    try:
        memory = psutil.virtual_memory()
        if memory.percent > max_percent:
            return False, f"Utilisation mémoire élevée: {memory.percent:.1f}%"
        return True, f"Utilisation mémoire OK: {memory.percent:.1f}%"
    except Exception as e:
        return False, f"Erreur lors de la vérification: {e}"
