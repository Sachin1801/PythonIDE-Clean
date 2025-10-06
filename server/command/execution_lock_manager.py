#!/usr/bin/env python3
"""
Execution Lock Manager - Prevents concurrent execution of the same file
Uses file-based locks to ensure only one process runs per Python file at a time
"""

import threading
import time
import os
from collections import defaultdict


class ExecutionLockManager:
    """Manages execution locks to prevent race conditions in file execution"""

    def __init__(self):
        self._locks = defaultdict(threading.Lock)  # Per-(user+file) locks
        self._active_executions = {}  # Track active executions: (user, file_path) -> (cmd_id, timestamp)
        self._cleanup_lock = threading.Lock()  # For cleanup operations

    def acquire_execution_lock(self, username, file_path, cmd_id, timeout=1.0):
        """
        Acquire execution lock for a specific user+file combination.
        Returns True if lock acquired, False if timeout
        """
        normalized_path = os.path.normpath(file_path)
        user_file_key = f"{username}:{normalized_path}"
        file_lock = self._locks[user_file_key]

        print(f"[EXEC-LOCK] Attempting to acquire lock for user {username}, file {normalized_path}, cmd_id: {cmd_id}")

        acquired = file_lock.acquire(timeout=timeout)
        if acquired:
            with self._cleanup_lock:
                # Check if there's already an active execution for this user+file
                if user_file_key in self._active_executions:
                    old_cmd_id, old_timestamp = self._active_executions[user_file_key]
                    print(
                        f"[EXEC-LOCK] Found existing execution for {user_file_key}: cmd_id={old_cmd_id}, replacing with {cmd_id}"
                    )

                # Register this execution
                self._active_executions[user_file_key] = (cmd_id, time.time())
                print(f"[EXEC-LOCK] Lock acquired for {user_file_key}, cmd_id: {cmd_id}")
                return True
        else:
            print(f"[EXEC-LOCK] Failed to acquire lock for {user_file_key}, cmd_id: {cmd_id} (timeout)")
            return False

    def release_execution_lock(self, username, file_path, cmd_id):
        """Release execution lock for a specific user+file combination"""
        normalized_path = os.path.normpath(file_path)
        user_file_key = f"{username}:{normalized_path}"

        with self._cleanup_lock:
            if user_file_key in self._active_executions:
                active_cmd_id, _ = self._active_executions[user_file_key]
                if active_cmd_id == cmd_id:
                    del self._active_executions[user_file_key]
                    print(f"[EXEC-LOCK] Released execution record for {user_file_key}, cmd_id: {cmd_id}")
                else:
                    print(
                        f"[EXEC-LOCK] WARNING: cmd_id mismatch for {user_file_key}: active={active_cmd_id}, releasing={cmd_id}"
                    )

        if user_file_key in self._locks:
            try:
                self._locks[user_file_key].release()
                print(f"[EXEC-LOCK] Lock released for {user_file_key}, cmd_id: {cmd_id}")
            except Exception as e:
                print(f"[EXEC-LOCK] Error releasing lock for {user_file_key}: {e}")

    def is_execution_active(self, username, file_path):
        """Check if there's an active execution for this user+file"""
        normalized_path = os.path.normpath(file_path)
        user_file_key = f"{username}:{normalized_path}"
        with self._cleanup_lock:
            return user_file_key in self._active_executions

    def get_active_execution(self, username, file_path):
        """Get active execution info for a user+file"""
        normalized_path = os.path.normpath(file_path)
        user_file_key = f"{username}:{normalized_path}"
        with self._cleanup_lock:
            return self._active_executions.get(user_file_key)

    def cleanup_old_executions(self, max_age_seconds=60):
        """Clean up old execution records (safety mechanism)"""
        current_time = time.time()
        with self._cleanup_lock:
            to_remove = []
            for user_file_key, (cmd_id, timestamp) in self._active_executions.items():
                if current_time - timestamp > max_age_seconds:
                    print(f"[EXEC-LOCK] Cleaning up old execution: {user_file_key}, cmd_id: {cmd_id}")
                    to_remove.append(user_file_key)

            for user_file_key in to_remove:
                del self._active_executions[user_file_key]
                # Try to release the lock if it's stuck
                try:
                    if user_file_key in self._locks:
                        self._locks[user_file_key].release()
                except:
                    pass


# Global instance
execution_lock_manager = ExecutionLockManager()
