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
        self._heartbeats = {}  # Track heartbeats: (user, file_path) -> last_heartbeat_time
        self._executors = {}  # Track executor references: (user, file_path) -> executor_ref

    def acquire_execution_lock(self, username, file_path, cmd_id, timeout=1.0, executor_ref=None):
        """
        Acquire execution lock for a specific user+file combination.
        Returns True if lock acquired, False if timeout
        executor_ref: Reference to the executor for health checking
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
                self._heartbeats[user_file_key] = time.time()
                if executor_ref:
                    self._executors[user_file_key] = executor_ref
                print(f"[EXEC-LOCK] ✅ Lock acquired for {user_file_key}, cmd_id: {cmd_id}")

                # Set up health check timer instead of auto-release
                def health_check_timer():
                    """Check if executor is still alive every 5 seconds"""
                    check_interval = 5.0  # Check every 5 seconds
                    max_stale_time = 30.0  # Consider dead if no heartbeat for 30 seconds

                    while True:
                        time.sleep(check_interval)
                        with self._cleanup_lock:
                            if user_file_key not in self._active_executions:
                                # Lock already released, stop checking
                                break

                            current_cmd_id, _ = self._active_executions.get(user_file_key, (None, None))
                            if current_cmd_id != cmd_id:
                                # Different execution now, stop checking
                                break

                            # Check if executor is still alive
                            executor = self._executors.get(user_file_key)
                            if executor:
                                # Check if executor thread is alive and not terminated
                                if hasattr(executor, 'alive') and not executor.alive:
                                    print(f"[EXEC-LOCK] 💀 Executor dead for {user_file_key}, releasing lock")
                                    self.release_execution_lock(username, normalized_path, cmd_id)
                                    break
                                elif hasattr(executor, 'is_alive') and not executor.is_alive():
                                    print(f"[EXEC-LOCK] 💀 Executor thread dead for {user_file_key}, releasing lock")
                                    self.release_execution_lock(username, normalized_path, cmd_id)
                                    break
                                # If waiting for input, don't check heartbeat timeout
                                elif hasattr(executor, 'waiting_for_input') and executor.waiting_for_input:
                                    # Update heartbeat when waiting for input (legitimate wait)
                                    self._heartbeats[user_file_key] = time.time()
                                    continue

                            # Check heartbeat staleness (only if not waiting for input)
                            last_heartbeat = self._heartbeats.get(user_file_key, 0)
                            if time.time() - last_heartbeat > max_stale_time:
                                print(f"[EXEC-LOCK] ⏰ No heartbeat for {max_stale_time}s, releasing lock for {user_file_key}")
                                self.release_execution_lock(username, normalized_path, cmd_id)
                                break

                # Start health check timer in background
                timer_thread = threading.Thread(target=health_check_timer, daemon=True, name=f"HealthCheck-{cmd_id}")
                timer_thread.start()

                return True
        else:
            print(f"[EXEC-LOCK] ❌ Failed to acquire lock for {user_file_key}, cmd_id: {cmd_id} (timeout)")
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
                    # Clean up tracking data
                    if user_file_key in self._heartbeats:
                        del self._heartbeats[user_file_key]
                    if user_file_key in self._executors:
                        del self._executors[user_file_key]
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

    def update_heartbeat(self, username, file_path):
        """Update heartbeat for an active execution"""
        normalized_path = os.path.normpath(file_path)
        user_file_key = f"{username}:{normalized_path}"
        with self._cleanup_lock:
            if user_file_key in self._heartbeats:
                self._heartbeats[user_file_key] = time.time()

    def release_all_user_locks(self, username):
        """Release all locks held by a specific user (useful for WebSocket disconnect)"""
        with self._cleanup_lock:
            keys_to_remove = []
            for user_file_key in list(self._active_executions.keys()):
                if user_file_key.startswith(f"{username}:"):
                    keys_to_remove.append(user_file_key)

            for key in keys_to_remove:
                cmd_id, _ = self._active_executions.get(key, (None, None))
                if key in self._locks:
                    try:
                        self._locks[key].release()
                    except:
                        pass  # Lock might not be held
                del self._active_executions[key]
                # Clean up tracking data
                if key in self._heartbeats:
                    del self._heartbeats[key]
                if key in self._executors:
                    del self._executors[key]
                print(f"[EXEC-LOCK] 🔓 Released lock for disconnected user: {key}, cmd_id: {cmd_id}")

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
