"""
Gestionnaire de backup optimisé avec système asynchrone et cache
Améliore les performances en évitant les backups inutiles
"""
import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Gestionnaire de backup avec système asynchrone et cache
    
    Caractéristiques:
    - Backup périodique automatique (toutes les X minutes)
    - Backup immédiat pour opérations critiques
    - Cache pour éviter les backups redondants
    - Thread-safe pour utilisation multi-thread
    """
    
    def __init__(
        self,
        backup_file: str = "events_data.json",
        backup_interval_minutes: int = 5,
        enable_async: bool = True
    ):
        """
        Initialise le gestionnaire de backup
        
        Args:
            backup_file: Chemin du fichier de backup
            backup_interval_minutes: Intervalle entre backups automatiques (minutes)
            enable_async: Activer le backup asynchrone
        """
        self.backup_file = backup_file
        self.backup_interval = timedelta(minutes=backup_interval_minutes)
        self.enable_async = enable_async
        
        # État du backup
        self.last_backup: Optional[datetime] = None
        self.last_backup_hash: Optional[str] = None
        self.pending_changes: bool = False
        self.backup_lock = threading.Lock()
        
        # Thread de backup
        self._backup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        
        # Callback pour récupérer les données
        self._data_callback: Optional[Callable[[], Dict[str, Any]]] = None
    
    def set_data_callback(self, callback: Callable[[], Dict[str, Any]]):
        """
        Définit la fonction callback pour récupérer les données à sauvegarder
        
        Args:
            callback: Fonction qui retourne un dictionnaire de données
        """
        self._data_callback = callback
    
    def start(self):
        """Démarre le service de backup en arrière-plan"""
        if not self.enable_async:
            logger.info("Backup asynchrone désactivé")
            return
        
        if self._running:
            logger.warning("Le service de backup est déjà démarré")
            return
        
        self._stop_event.clear()
        self._running = True
        self._backup_thread = threading.Thread(
            target=self._backup_loop,
            daemon=True,
            name="BackupManager"
        )
        self._backup_thread.start()
        logger.info(f"Service de backup démarré (intervalle: {self.backup_interval})")
    
    def stop(self, timeout: float = 5.0):
        """
        Arrête le service de backup
        
        Args:
            timeout: Temps d'attente maximum pour l'arrêt (secondes)
        """
        if not self._running:
            return
        
        logger.info("Arrêt du service de backup...")
        self._running = False
        self._stop_event.set()
        
        if self._backup_thread and self._backup_thread.is_alive():
            self._backup_thread.join(timeout=timeout)
            if self._backup_thread.is_alive():
                logger.warning("Le thread de backup n'a pas pu être arrêté dans le délai")
            else:
                logger.info("Service de backup arrêté")
    
    def request_backup(self, immediate: bool = False):
        """
        Demande un backup
        
        Args:
            immediate: Si True, force un backup immédiat (pour opérations critiques)
        """
        with self.backup_lock:
            self.pending_changes = True
        
        if immediate:
            logger.debug("Backup immédiat demandé")
            self._perform_backup()
        else:
            logger.debug("Backup planifié")
    
    def _backup_loop(self):
        """Boucle principale du backup périodique"""
        logger.info("Boucle de backup démarrée")
        
        while self._running and not self._stop_event.is_set():
            try:
                # Vérifier si un backup est nécessaire
                if self._should_backup():
                    self._perform_backup()
                
                # Attendre l'intervalle ou jusqu'à l'arrêt
                wait_time = self.backup_interval.total_seconds()
                if self._stop_event.wait(wait_time):
                    break  # Arrêt demandé
                    
            except Exception as e:
                logger.error(f"Erreur dans la boucle de backup: {e}", exc_info=True)
                # Attendre 1 minute en cas d'erreur avant de réessayer
                time.sleep(60)
        
        logger.info("Boucle de backup terminée")
    
    def _should_backup(self) -> bool:
        """
        Détermine si un backup est nécessaire
        
        Returns:
            True si un backup doit être effectué
        """
        with self.backup_lock:
            # Si des changements sont en attente
            if self.pending_changes:
                return True
            
            # Si aucun backup n'a jamais été fait
            if self.last_backup is None:
                return True
            
            # Si l'intervalle de temps est dépassé
            if datetime.now() - self.last_backup >= self.backup_interval:
                return True
        
        return False
    
    def _perform_backup(self):
        """
        Effectue le backup des données
        
        Returns:
            True si le backup a réussi, False sinon
        """
        if not self._data_callback:
            logger.warning("Aucun callback de données défini, impossible de faire le backup")
            return False
        
        try:
            # Récupérer les données
            logger.debug("Récupération des données pour le backup...")
            data = self._data_callback()
            
            if not data:
                logger.warning("Aucune donnée à sauvegarder")
                return False
            
            # Calculer le hash des données pour éviter les backups inutiles
            import hashlib
            data_json = json.dumps(data, sort_keys=True, ensure_ascii=False)
            data_hash = hashlib.md5(data_json.encode('utf-8')).hexdigest()
            
            # Vérifier si les données ont changé
            with self.backup_lock:
                if data_hash == self.last_backup_hash:
                    logger.debug("Aucun changement détecté, backup ignoré")
                    self.pending_changes = False
                    return True
            
            # Créer le backup
            logger.info(f"Création du backup vers {self.backup_file}...")
            
            # Créer le répertoire si nécessaire
            backup_path = Path(self.backup_file)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Écrire le fichier de manière atomique (écriture dans un fichier temporaire puis renommage)
            temp_file = f"{self.backup_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Renommer atomiquement
            if os.path.exists(self.backup_file):
                os.replace(temp_file, self.backup_file)
            else:
                os.rename(temp_file, self.backup_file)
            
            # Mettre à jour l'état
            with self.backup_lock:
                self.last_backup = datetime.now()
                self.last_backup_hash = data_hash
                self.pending_changes = False
            
            file_size = os.path.getsize(self.backup_file) / 1024  # KB
            logger.info(f"Backup créé avec succès ({file_size:.2f} KB) à {self.last_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du backup: {e}", exc_info=True)
            with self.backup_lock:
                self.pending_changes = True  # Réessayer plus tard
            return False
    
    def get_backup_info(self) -> Dict[str, Any]:
        """
        Retourne des informations sur l'état du backup
        
        Returns:
            Dictionnaire avec les informations du backup
        """
        with self.backup_lock:
            return {
                'last_backup': self.last_backup.isoformat() if self.last_backup else None,
                'pending_changes': self.pending_changes,
                'backup_file': self.backup_file,
                'backup_interval_minutes': self.backup_interval.total_seconds() / 60,
                'running': self._running,
                'file_exists': os.path.exists(self.backup_file),
                'file_size_kb': os.path.getsize(self.backup_file) / 1024 if os.path.exists(self.backup_file) else 0
            }
    
    def force_backup_now(self) -> bool:
        """
        Force un backup immédiat (synchronisé)
        
        Returns:
            True si le backup a réussi
        """
        logger.info("Backup forcé immédiatement")
        return self._perform_backup()


# ============================================================================
# INSTANCE GLOBALE (SINGLETON)
# ============================================================================

_backup_manager_instance: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """
    Obtient l'instance globale du gestionnaire de backup (singleton)
    
    Returns:
        Instance du BackupManager
    """
    global _backup_manager_instance
    if _backup_manager_instance is None:
        _backup_manager_instance = BackupManager()
    return _backup_manager_instance
