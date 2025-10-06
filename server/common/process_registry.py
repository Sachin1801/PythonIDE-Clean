#!/usr/bin/env python3
"""
Process Registry for tracking user execution processes
Designed for 38 concurrent users with resource monitoring
"""

import threading
import time
import psutil
import os
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a tracked process"""

    pid: int
    username: str
    file_path: Optional[str]
    process_type: str  # 'script', 'repl', 'interactive'
    start_time: float
    last_activity: float
    memory_mb: float
    cpu_percent: float
    cmd_id: str

    def to_dict(self):
        return asdict(self)

    def age_seconds(self) -> float:
        return time.time() - self.start_time

    def idle_seconds(self) -> float:
        return time.time() - self.last_activity


class ProcessRegistry:
    """
    Central registry for all user execution processes
    Tracks resources, limits, and cleanup for 38 concurrent users
    """

    def __init__(self):
        # Process tracking
        self._processes: Dict[int, ProcessInfo] = {}  # pid -> ProcessInfo
        self._user_processes: Dict[str, List[int]] = {}  # username -> [pid, pid, ...]
        self._lock = threading.RLock()

        # Resource limits for 38 users
        self.MAX_CONCURRENT_USERS = 38
        self.MAX_PROCESSES_PER_USER = 3  # 1 script + 1 REPL + 1 file op
        self.MAX_TOTAL_PROCESSES = 114  # 38 × 3

        # Memory limits (4GB total, 1GB for server = 3GB for user processes)
        self.MAX_TOTAL_MEMORY_MB = 3000
        self.MAX_MEMORY_PER_PROCESS_MB = 50  # Conservative limit

        # Process age limits
        self.MAX_SCRIPT_AGE_SECONDS = 300  # 5 minutes for scripts
        self.MAX_REPL_IDLE_SECONDS = 1800  # 30 minutes idle for REPL
        self.MAX_INTERACTIVE_AGE_SECONDS = 600  # 10 minutes for file operations

        # Monitoring
        self._cleanup_interval = 60  # Check every minute
        self._stats_interval = 30  # Update stats every 30s

        # Start background services
        self._start_background_services()

        logger.info(f"ProcessRegistry initialized for {self.MAX_CONCURRENT_USERS} users")

    def register_process(
        self, pid: int, username: str, file_path: Optional[str], process_type: str, cmd_id: str
    ) -> bool:
        """
        Register a new user process
        Returns False if limits exceeded
        """
        with self._lock:
            # Check user process limit
            user_process_count = len(self._user_processes.get(username, []))
            if user_process_count >= self.MAX_PROCESSES_PER_USER:
                logger.warning(f"User {username} exceeded process limit ({user_process_count})")
                return False

            # Check total process limit
            if len(self._processes) >= self.MAX_TOTAL_PROCESSES:
                logger.warning(f"Total process limit exceeded ({len(self._processes)})")
                return False

            # Get process info
            try:
                proc = psutil.Process(pid)
                memory_mb = proc.memory_info().rss / 1024 / 1024
                cpu_percent = proc.cpu_percent()
            except psutil.NoSuchProcess:
                logger.error(f"Process {pid} not found during registration")
                return False

            # Check memory limit
            total_memory = sum(p.memory_mb for p in self._processes.values())
            if total_memory + memory_mb > self.MAX_TOTAL_MEMORY_MB:
                logger.warning(f"Memory limit would be exceeded: {total_memory + memory_mb}MB")
                return False

            # Create process info
            current_time = time.time()
            process_info = ProcessInfo(
                pid=pid,
                username=username,
                file_path=file_path,
                process_type=process_type,
                start_time=current_time,
                last_activity=current_time,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                cmd_id=cmd_id,
            )

            # Register process
            self._processes[pid] = process_info

            # Track by user
            if username not in self._user_processes:
                self._user_processes[username] = []
            self._user_processes[username].append(pid)

            logger.info(f"Registered {process_type} process {pid} for {username} ({cmd_id})")
            return True

    def unregister_process(self, pid: int):
        """Remove process from registry"""
        with self._lock:
            if pid in self._processes:
                process_info = self._processes[pid]
                username = process_info.username

                # Remove from main registry
                del self._processes[pid]

                # Remove from user tracking
                if username in self._user_processes:
                    if pid in self._user_processes[username]:
                        self._user_processes[username].remove(pid)

                    # Clean up empty user entries
                    if not self._user_processes[username]:
                        del self._user_processes[username]

                logger.info(f"Unregistered process {pid} for {username}")

    def update_activity(self, pid: int):
        """Update last activity time for a process"""
        with self._lock:
            if pid in self._processes:
                self._processes[pid].last_activity = time.time()

    def get_user_processes(self, username: str) -> List[ProcessInfo]:
        """Get all processes for a user"""
        with self._lock:
            user_pids = self._user_processes.get(username, [])
            return [self._processes[pid] for pid in user_pids if pid in self._processes]

    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        with self._lock:
            stats = {
                "total_processes": len(self._processes),
                "active_users": len(self._user_processes),
                "total_memory_mb": sum(p.memory_mb for p in self._processes.values()),
                "processes_by_type": {},
                "processes_by_user": {},
                "resource_limits": {
                    "max_users": self.MAX_CONCURRENT_USERS,
                    "max_processes": self.MAX_TOTAL_PROCESSES,
                    "max_memory_mb": self.MAX_TOTAL_MEMORY_MB,
                },
                "timestamp": time.time(),
            }

            # Count by type
            for process in self._processes.values():
                ptype = process.process_type
                if ptype not in stats["processes_by_type"]:
                    stats["processes_by_type"][ptype] = 0
                stats["processes_by_type"][ptype] += 1

            # Count by user
            for username, pids in self._user_processes.items():
                stats["processes_by_user"][username] = len(pids)

            return stats

    def cleanup_expired_processes(self):
        """Clean up expired processes based on age and type"""
        current_time = time.time()
        cleanup_count = 0

        with self._lock:
            expired_pids = []

            for pid, process_info in self._processes.items():
                should_cleanup = False
                reason = ""

                try:
                    # Check if process still exists
                    proc = psutil.Process(pid)

                    # Update resource usage
                    process_info.memory_mb = proc.memory_info().rss / 1024 / 1024
                    process_info.cpu_percent = proc.cpu_percent()

                    # Check age limits by process type
                    age = process_info.age_seconds()
                    idle = process_info.idle_seconds()

                    if process_info.process_type == "script":
                        if age > self.MAX_SCRIPT_AGE_SECONDS:
                            should_cleanup = True
                            reason = f"script timeout ({int(age)}s)"

                    elif process_info.process_type == "repl":
                        if idle > self.MAX_REPL_IDLE_SECONDS:
                            should_cleanup = True
                            reason = f"REPL idle timeout ({int(idle)}s)"

                    elif process_info.process_type == "interactive":
                        if age > self.MAX_INTERACTIVE_AGE_SECONDS:
                            should_cleanup = True
                            reason = f"interactive timeout ({int(age)}s)"

                    # Check memory limit
                    if process_info.memory_mb > self.MAX_MEMORY_PER_PROCESS_MB:
                        should_cleanup = True
                        reason = f"memory limit ({process_info.memory_mb:.1f}MB)"

                    if should_cleanup:
                        try:
                            proc.kill()
                            expired_pids.append(pid)
                            cleanup_count += 1
                            logger.info(f"Killed process {pid} ({process_info.username}): {reason}")
                        except psutil.NoSuchProcess:
                            expired_pids.append(pid)
                        except Exception as e:
                            logger.error(f"Failed to kill process {pid}: {e}")

                except psutil.NoSuchProcess:
                    # Process already terminated
                    expired_pids.append(pid)
                except Exception as e:
                    logger.error(f"Error checking process {pid}: {e}")

            # Remove expired processes from registry
            for pid in expired_pids:
                self.unregister_process(pid)

        if cleanup_count > 0:
            logger.info(f"Process cleanup: terminated {cleanup_count} expired processes")

        return cleanup_count

    def _start_background_services(self):
        """Start background monitoring and cleanup services"""

        def cleanup_loop():
            while True:
                try:
                    time.sleep(self._cleanup_interval)
                    self.cleanup_expired_processes()
                except Exception as e:
                    logger.error(f"Error in cleanup loop: {e}")

        def stats_loop():
            while True:
                try:
                    time.sleep(self._stats_interval)
                    stats = self.get_system_stats()

                    # Log warnings if approaching limits
                    if stats["total_processes"] > self.MAX_TOTAL_PROCESSES * 0.8:
                        logger.warning(f"High process count: {stats['total_processes']}/{self.MAX_TOTAL_PROCESSES}")

                    if stats["total_memory_mb"] > self.MAX_TOTAL_MEMORY_MB * 0.8:
                        logger.warning(
                            f"High memory usage: {stats['total_memory_mb']:.1f}MB/{self.MAX_TOTAL_MEMORY_MB}MB"
                        )

                except Exception as e:
                    logger.error(f"Error in stats loop: {e}")

        # Start daemon threads
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()

        stats_thread = threading.Thread(target=stats_loop, daemon=True)
        stats_thread.start()

        logger.info("Background services started (cleanup and stats monitoring)")


# Global instance
process_registry = ProcessRegistry()
