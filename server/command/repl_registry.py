"""
Global REPL Process Registry
Manages persistent REPL processes across WebSocket reconnections
"""

import threading
import time
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from .hybrid_repl_thread import HybridREPLThread

logger = logging.getLogger(__name__)


class REPLRegistry:
    """
    Singleton registry for managing REPL processes by user and file.
    Ensures REPL processes persist across WebSocket reconnections.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(REPLRegistry, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._processes: Dict[str, Dict[str, Tuple[HybridREPLThread, datetime]]] = {}
        # Structure: {username: {file_path: (repl_thread, last_access_time)}}
        
        self._process_lock = threading.RLock()
        self._cleanup_interval = 60  # Check every minute
        self._max_idle_time = 3600   # 60 minutes idle timeout
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_expired_processes,
            daemon=True
        )
        self._cleanup_thread.start()
        
        self._initialized = True
        logger.info("REPL Registry initialized")
    
    def get_or_create_repl(self, username: str, file_path: Optional[str], 
                          cmd_id: str, client, loop) -> HybridREPLThread:
        """
        Get existing REPL process or create new one.
        
        Args:
            username: User identifier
            file_path: File being executed (None for empty REPL)
            cmd_id: Command ID for this execution
            client: WebSocket client
            loop: Event loop
            
        Returns:
            HybridREPLThread instance (existing or new)
        """
        with self._process_lock:
            # Use file_path or 'empty_repl' as key
            repl_key = file_path if file_path else 'empty_repl'
            
            # Initialize user entry if doesn't exist
            if username not in self._processes:
                self._processes[username] = {}
            
            user_repls = self._processes[username]
            
            # Check if REPL exists and is still alive
            if repl_key in user_repls:
                existing_repl, last_access = user_repls[repl_key]
                
                if existing_repl.is_alive():
                    # Update last access time and client reference
                    user_repls[repl_key] = (existing_repl, datetime.now())
                    existing_repl.update_client(client, cmd_id)
                    
                    logger.info(f"Reconnected to existing REPL: user={username}, file={repl_key}")
                    return existing_repl
                else:
                    # Process died, remove it
                    logger.info(f"Removing dead REPL process: user={username}, file={repl_key}")
                    del user_repls[repl_key]
            
            # Create new REPL process
            logger.info(f"Creating new REPL process: user={username}, file={repl_key}")
            new_repl = HybridREPLThread(
                cmd_id=cmd_id,
                client=client,
                event_loop=loop,
                script_path=file_path,
                registry_callback=self._on_repl_finished
            )
            
            # Store in registry
            user_repls[repl_key] = (new_repl, datetime.now())
            
            return new_repl
    
    def update_repl_access(self, username: str, file_path: Optional[str]):
        """Update last access time for a REPL process."""
        with self._process_lock:
            repl_key = file_path if file_path else 'empty_repl'
            
            if username in self._processes and repl_key in self._processes[username]:
                repl_thread, _ = self._processes[username][repl_key]
                self._processes[username][repl_key] = (repl_thread, datetime.now())
    
    def terminate_repl(self, username: str, file_path: Optional[str]) -> bool:
        """
        Manually terminate a REPL process.
        
        Returns:
            True if process was found and terminated, False otherwise
        """
        with self._process_lock:
            repl_key = file_path if file_path else 'empty_repl'
            
            if username in self._processes and repl_key in self._processes[username]:
                repl_thread, _ = self._processes[username][repl_key]
                
                try:
                    repl_thread.stop()
                    del self._processes[username][repl_key]
                    
                    # Clean up empty user entry
                    if not self._processes[username]:
                        del self._processes[username]
                    
                    logger.info(f"Terminated REPL: user={username}, file={repl_key}")
                    return True
                except Exception as e:
                    logger.error(f"Error terminating REPL: {e}")
                    return False
            
            return False
    
    def get_user_repls(self, username: str) -> Dict[str, Tuple[bool, datetime]]:
        """
        Get status of all REPL processes for a user.
        
        Returns:
            Dict mapping file paths to (is_alive, last_access) tuples
        """
        with self._process_lock:
            if username not in self._processes:
                return {}
            
            result = {}
            for file_path, (repl_thread, last_access) in self._processes[username].items():
                result[file_path] = (repl_thread.is_alive(), last_access)
            
            return result
    
    def _on_repl_finished(self, username: str, file_path: Optional[str]):
        """Callback when REPL process finishes naturally."""
        with self._process_lock:
            repl_key = file_path if file_path else 'empty_repl'
            
            if username in self._processes and repl_key in self._processes[username]:
                logger.info(f"REPL process finished: user={username}, file={repl_key}")
                del self._processes[username][repl_key]
                
                # Clean up empty user entry
                if not self._processes[username]:
                    del self._processes[username]
    
    def _cleanup_expired_processes(self):
        """Background thread to clean up expired REPL processes."""
        while True:
            try:
                time.sleep(self._cleanup_interval)
                self._perform_cleanup()
            except Exception as e:
                logger.error(f"Error in REPL cleanup thread: {e}")
    
    def _perform_cleanup(self):
        """Clean up expired or dead REPL processes."""
        with self._process_lock:
            current_time = datetime.now()
            expired_processes = []
            
            # Find expired processes
            for username, user_repls in self._processes.items():
                for file_path, (repl_thread, last_access) in user_repls.items():
                    # Check if process is dead or expired
                    if not repl_thread.is_alive():
                        expired_processes.append((username, file_path, "dead"))
                    elif current_time - last_access > timedelta(seconds=self._max_idle_time):
                        expired_processes.append((username, file_path, "expired"))
            
            # Clean up expired processes
            for username, file_path, reason in expired_processes:
                try:
                    repl_thread, _ = self._processes[username][file_path]
                    
                    if reason == "expired" and repl_thread.is_alive():
                        repl_thread.stop()
                    
                    del self._processes[username][file_path]
                    
                    # Clean up empty user entry
                    if not self._processes[username]:
                        del self._processes[username]
                    
                    logger.info(f"Cleaned up {reason} REPL: user={username}, file={file_path}")
                    
                except Exception as e:
                    logger.error(f"Error cleaning up REPL {username}/{file_path}: {e}")
    
    def get_stats(self) -> Dict:
        """Get registry statistics."""
        with self._process_lock:
            total_processes = sum(len(user_repls) for user_repls in self._processes.values())
            active_processes = 0
            
            for user_repls in self._processes.values():
                for repl_thread, _ in user_repls.values():
                    if repl_thread.is_alive():
                        active_processes += 1
            
            return {
                'total_users': len(self._processes),
                'total_processes': total_processes,
                'active_processes': active_processes,
                'cleanup_interval': self._cleanup_interval,
                'max_idle_time': self._max_idle_time
            }


# Global singleton instance
repl_registry = REPLRegistry()