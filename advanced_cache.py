"""
Système de cache avancé avec invalidation intelligente
- Cache multi-niveaux
- TTL configurable
- Invalidation par tags
- Statistiques de cache
"""
import time
import hashlib
import json
from typing import Any, Optional, Dict, List, Callable, Set
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
import logging
import threading

logger = logging.getLogger(__name__)


class CacheEntry:
    """Entrée de cache avec métadonnées"""
    
    def __init__(self, value: Any, ttl: float, tags: Set[str] = None):
        """
        Initialise une entrée de cache
        
        Args:
            value: Valeur à mettre en cache
            ttl: Time to live en secondes
            tags: Tags pour invalidation groupée
        """
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl
        self.tags = tags or set()
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Vérifie si l'entrée est expirée"""
        return time.time() > self.expires_at
    
    def access(self):
        """Enregistre un accès"""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation"""
        return {
            'value': self.value,
            'created_at': datetime.fromtimestamp(self.created_at).isoformat(),
            'expires_at': datetime.fromtimestamp(self.expires_at).isoformat(),
            'tags': list(self.tags),
            'access_count': self.access_count,
            'last_accessed': datetime.fromtimestamp(self.last_accessed).isoformat()
        }


class AdvancedCache:
    """
    Cache avancé avec invalidation intelligente et statistiques
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        """
        Initialise le cache
        
        Args:
            max_size: Taille maximale du cache
            default_ttl: TTL par défaut en secondes
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)  # tag -> set of keys
        self.lock = threading.RLock()
        
        # Statistiques
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'invalidations': 0
        }
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Génère une clé de cache à partir des arguments"""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache
        
        Args:
            key: Clé de cache
        
        Returns:
            Valeur en cache ou None
        """
        with self.lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            entry = self.cache[key]
            
            if entry.is_expired():
                # Supprimer l'entrée expirée
                self._remove_entry(key)
                self.stats['misses'] += 1
                return None
            
            entry.access()
            self.stats['hits'] += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None, tags: Set[str] = None):
        """
        Met une valeur en cache
        
        Args:
            key: Clé de cache
            value: Valeur à mettre en cache
            ttl: Time to live (utilise default_ttl si None)
            tags: Tags pour invalidation groupée
        """
        with self.lock:
            # Éviction si nécessaire
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_oldest()
            
            ttl = ttl or self.default_ttl
            entry = CacheEntry(value, ttl, tags)
            
            # Mettre à jour l'index des tags
            if tags:
                for tag in tags:
                    self.tag_index[tag].add(key)
            
            self.cache[key] = entry
            self.stats['sets'] += 1
    
    def delete(self, key: str):
        """Supprime une entrée du cache"""
        with self.lock:
            self._remove_entry(key)
    
    def _remove_entry(self, key: str):
        """Supprime une entrée et met à jour les index"""
        if key in self.cache:
            entry = self.cache[key]
            # Retirer des tags
            for tag in entry.tags:
                self.tag_index[tag].discard(key)
                if not self.tag_index[tag]:
                    del self.tag_index[tag]
            del self.cache[key]
    
    def invalidate_by_tag(self, tag: str):
        """
        Invalide toutes les entrées avec un tag spécifique
        
        Args:
            tag: Tag à invalider
        """
        with self.lock:
            if tag not in self.tag_index:
                return
            
            keys_to_remove = list(self.tag_index[tag])
            for key in keys_to_remove:
                self._remove_entry(key)
            
            self.stats['invalidations'] += len(keys_to_remove)
            logger.info(f"Invalidé {len(keys_to_remove)} entrées avec le tag '{tag}'")
    
    def invalidate_by_tags(self, tags: Set[str]):
        """Invalide toutes les entrées avec n'importe lequel des tags"""
        for tag in tags:
            self.invalidate_by_tag(tag)
    
    def clear(self):
        """Vide complètement le cache"""
        with self.lock:
            self.cache.clear()
            self.tag_index.clear()
            self.stats['invalidations'] += len(self.cache)
    
    def _evict_oldest(self):
        """Évince l'entrée la plus ancienne (LRU)"""
        if not self.cache:
            return
        
        # Trouver l'entrée la moins récemment utilisée
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed
        )
        self._remove_entry(oldest_key)
        self.stats['evictions'] += 1
    
    def cleanup_expired(self):
        """Nettoie toutes les entrées expirées"""
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                self._remove_entry(key)
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate': f"{hit_rate:.2f}%",
                'sets': self.stats['sets'],
                'evictions': self.stats['evictions'],
                'invalidations': self.stats['invalidations'],
                'tags_count': len(self.tag_index)
            }


# Instance globale
_global_cache = AdvancedCache(max_size=1000, default_ttl=3600)


def cached(ttl: float = 3600, tags: Set[str] = None, cache_instance: AdvancedCache = None):
    """
    Décorateur pour mettre en cache le résultat d'une fonction
    
    Usage:
        @cached(ttl=600, tags={'events'})
        def get_all_events():
            ...
    """
    cache = cache_instance or _global_cache
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Générer la clé de cache
            cache_key = cache._generate_key(func.__name__, *args, **kwargs)
            
            # Essayer de récupérer du cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Exécuter la fonction et mettre en cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl, tags=tags)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_by_tag(tag: str, cache_instance: AdvancedCache = None):
    """
    Invalide le cache par tag
    
    Usage:
        invalidate_cache_by_tag('events')  # Après modification d'événements
    """
    cache = cache_instance or _global_cache
    cache.invalidate_by_tag(tag)
