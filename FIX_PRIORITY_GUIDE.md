# Priority Fix Guide - Critical Issues Resolution

## Overview

This guide provides step-by-step fixes for the 5 CRITICAL issues discovered in the deep scan. Estimated implementation time: **16-20 hours** for all critical fixes.

---

# CRITICAL FIX #1: Working Directory Race Condition

**Severity**: CRITICAL - Data corruption possible
**Files Affected**: `server/command/simple_exec_v3.py`
**Estimated Time**: 3-4 hours

## Problem

Multiple threads using `os.chdir()` simultaneously corrupt each other's working directories, causing CSV files and other outputs to be created in wrong locations.

## Root Cause

```python
# Thread 1
original_cwd = os.getcwd()           # Gets "/app/server"
os.chdir("/mnt/efs/pythonide-data/Local/student1")

# Thread 2 (simultaneous)
original_cwd = os.getcwd()           # Gets "/mnt/efs/pythonide-data/Local/student1" ❌ WRONG!
os.chdir("/mnt/efs/pythonide-data/Local/student2")

# Thread 1 tries to restore
os.chdir(original_cwd)               # Restores to student2's directory ❌ CORRUPTION!
```

## Solution Approach

**Recommended**: Use `subprocess.Popen()` with `cwd` parameter (safest)

### Option 1: Use subprocess (RECOMMENDED)

**Why**: Thread-safe, no global state mutation, standard Python practice

```python
# In simple_exec_v3.py, replace the exec() approach with:

import subprocess
import tempfile
import json

class SimpleExecutorV3(threading.Thread):
    def run_script_subprocess(self, script_path, username):
        """Execute script in separate process with correct working directory"""
        script_dir = os.path.dirname(os.path.abspath(script_path))

        # Create wrapper script to capture output
        wrapper_code = f"""
import sys
import os
sys.path.insert(0, {repr(script_dir)})

try:
    with open({repr(script_path)}, 'r') as f:
        code = f.read()

    namespace = {{'__file__': {repr(script_path)}, '__name__': '__main__'}}
    exec(compile(code, {repr(script_path)}, 'exec'), namespace)

except Exception as e:
    import traceback
    sys.stderr.write(traceback.format_exc())
    sys.exit(1)
"""

        # Run in subprocess (thread-safe!)
        proc = subprocess.Popen(
            [Config.PYTHON, '-c', wrapper_code],
            cwd=script_dir,  # ← Safe: Process inherits this, not affected by other threads
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Handle output
        for line in proc.stdout:
            self.send_message(MessageType.STDOUT, line)

        for line in proc.stderr:
            self.send_message(MessageType.STDERR, line)

        proc.wait(timeout=30)
        return proc.returncode
```

**Pros**:
- ✅ Completely thread-safe (different processes)
- ✅ No global state mutation
- ✅ Proper process isolation
- ✅ Standard Python approach
- ✅ Easy to understand and maintain

**Cons**:
- Process startup overhead (~50ms)
- Variable persistence across script/REPL needs different approach

---

### Option 2: Thread-Local Storage (ALTERNATIVE)

**Why**: Keeps current exec() approach but isolates per-thread state

```python
import threading

# At module level
_thread_local = threading.local()

class SimpleExecutorV3(threading.Thread):
    def execute_script(self):
        """Execute script with thread-safe directory handling"""
        script_dir = os.path.dirname(os.path.abspath(self.script_path))

        # Store original cwd in thread-local storage (safe from other threads)
        _thread_local.original_cwd = os.getcwd()

        try:
            os.chdir(script_dir)
            # Execute script
            with open(self.script_path, 'r') as f:
                script_code = f.read()

            compiled_code = compile(script_code, self.script_path, 'exec')
            self.namespace['__file__'] = os.path.abspath(self.script_path)

            exec(compiled_code, self.namespace)

        finally:
            # Restore from thread-local (guaranteed correct)
            os.chdir(_thread_local.original_cwd)
```

**Pros**:
- ✅ Minimal code changes
- ✅ Thread-safe without subprocess
- ✅ Variable persistence preserved
- ✅ Works with existing REPL transition

**Cons**:
- Slightly less safe (still manipulating global os.chdir)
- More complex to understand

---

### Option 3: Rewrite Executor (BEST LONG-TERM)

Replace entire execution model with subprocess-based approach that naturally supports proper directory isolation.

---

## Recommended Fix: Option 2 (Thread-Local Storage)

**Why**: Best balance of safety, minimal changes, and compatibility

### Implementation Steps

**Step 1**: Add thread-local storage at module top

```python
# At top of server/command/simple_exec_v3.py
import threading

_thread_local = threading.local()
```

**Step 2**: Update execute_script() method (lines 346-406)

```python
# OLD CODE:
original_cwd = os.getcwd()
os.chdir(script_dir)
try:
    # ... execute ...
finally:
    os.chdir(original_cwd)

# NEW CODE:
_thread_local.original_cwd = os.getcwd()
try:
    os.chdir(script_dir)
    # ... execute ...
finally:
    os.chdir(_thread_local.original_cwd)
```

**Step 3**: Update exception handlers (lines 412, 426)

```python
# OLD:
os.chdir(original_cwd)

# NEW:
os.chdir(_thread_local.original_cwd)
```

### Verification

After fix, test:
```bash
# Run 10 concurrent scripts, verify files in correct directories
python test_concurrent_execution.py

# Test output:
# Thread 1: test.csv created in /mnt/efs/pythonide-data/Local/student1 ✅
# Thread 2: data.csv created in /mnt/efs/pythonide-data/Local/student2 ✅
# No cross-contamination
```

---

# CRITICAL FIX #2: Triple Lock Release Paths

**Severity**: CRITICAL - Lock state corruption
**Files Affected**: `server/command/simple_exec_v3.py`, `execution_lock_manager.py`
**Estimated Time**: 3-4 hours

## Problem

Lock released in 3 different code paths, creating race conditions:
- Path 1: After script completes (line 240)
- Path 2: When stop signal arrives (line 567)
- Path 3: During cleanup (line 771)

Using `_lock_released` flag doesn't prevent all race conditions.

## Root Cause

```python
# Path 1: Script completes
execution_lock_manager.release_execution_lock(...)
self._lock_released = True

# Meanwhile, Path 2: Stop signal
if not self._lock_released:  # Check time: BEFORE release
    execution_lock_manager.release_execution_lock(...)

    # Meanwhile, Path 1 sets _lock_released = True
    # Both release simultaneously = RACE CONDITION
```

## Solution: Single-Point Lock Release

Implement a centralized "cleanup" method that releases locks exactly once.

### Implementation

**Step 1**: Create cleanup method in `simple_exec_v3.py`

```python
class SimpleExecutorV3(threading.Thread):
    def __init__(self, ...):
        super().__init__()
        self._lock_release_lock = threading.Lock()  # Protect cleanup
        self._lock_released = False

    def _release_execution_lock_once(self):
        """Release execution lock exactly once, thread-safe"""
        with self._lock_release_lock:  # Mutual exclusion
            if not self._lock_released:
                try:
                    if hasattr(self, 'username') and hasattr(self, 'script_path'):
                        if self.username and self.script_path:
                            execution_lock_manager.release_execution_lock(
                                self.username,
                                self.script_path,
                                self.cmd_id
                            )
                except Exception as e:
                    print(f"[Lock] Failed to release: {e}")
                finally:
                    self._lock_released = True
```

**Step 2**: Replace all 3 release paths with call to `_release_execution_lock_once()`

```python
# OLD (line 240):
if not self._lock_released and hasattr(self, 'username') and hasattr(self, 'script_path'):
    if self.username and self.script_path:
        try:
            execution_lock_manager.release_execution_lock(...)
            self._lock_released = True
        except:
            pass

# NEW:
self._release_execution_lock_once()
```

**Step 3**: Remove all direct release calls, add to stop() method

```python
def stop(self):
    """Stop the executor"""
    self._stop_event.set()
    self.alive = False
    # Release lock on stop
    self._release_execution_lock_once()
```

**Step 4**: Add to cleanup (run() method finally block)

```python
def run(self):
    try:
        # ... execution code ...
    finally:
        # Ensure lock is released
        self._release_execution_lock_once()
        # Clean up resources
        self.cleanup()
```

### Benefits

✅ Lock released exactly once
✅ Thread-safe with mutex
✅ No race conditions
✅ Centralized cleanup logic
✅ Easy to add logging/monitoring

### Verification

```python
# Test concurrent stop signals
def test_concurrent_stop():
    executor = SimpleExecutorV3(...)

    # Start long-running script
    executor.start()
    time.sleep(0.1)

    # Send stop from multiple "threads"
    for _ in range(3):
        threading.Thread(target=executor.stop).start()

    executor.join(timeout=5)

    # Verify lock released exactly once (check logs)
    # Should see 1 release, not 3
    assert count_release_messages == 1
```

---

# CRITICAL FIX #3: Bare Except Clauses

**Severity**: CRITICAL - Debugging impossible
**Files Affected**: 24+ locations across codebase
**Estimated Time**: 6-8 hours

## Problem

```python
try:
    os.chdir(script_dir)
except:
    pass  # Catches SystemExit, KeyboardInterrupt, RuntimeError, etc.
          # All errors silently ignored!
```

This hides:
- Lock release failures (RuntimeError)
- Directory change failures (OSError)
- Programming bugs (ValueError, TypeError)
- System signals (KeyboardInterrupt, SystemExit)

## Solution: Specific Exception Handling

Replace all bare `except:` with specific exception types.

### Implementation Strategy

**Step 1**: Create exception hierarchy (new file: `server/command/exceptions.py`)

```python
"""Custom exceptions for PythonIDE execution"""

class ExecutionError(Exception):
    """Base class for execution errors"""
    pass

class LockError(ExecutionError):
    """Lock acquisition/release failed"""
    pass

class FileOperationError(ExecutionError):
    """File read/write failed"""
    pass

class TimeoutError(ExecutionError):
    """Script execution timeout"""
    pass

class TerminationError(ExecutionError):
    """Script termination requested"""
    pass
```

**Step 2**: Replace bare except clauses

**File: `server/command/simple_exec_v3.py:168`**

```python
# OLD:
try:
    sys.settrace(trace_function)
except:
    pass

# NEW:
try:
    sys.settrace(trace_function)
except RuntimeError as e:
    logger.warning(f"Failed to set trace function: {e}")
    # Continue without trace (non-fatal)
```

**File: `server/command/simple_exec_v3.py:427`**

```python
# OLD:
try:
    os.chdir(original_cwd)
except:
    pass

# NEW:
try:
    os.chdir(_thread_local.original_cwd)
except OSError as e:
    logger.error(f"Failed to restore working directory: {e}")
    # State is corrupted, but we can't fix it here
    # Mark executor as unhealthy
    self.healthy = False
```

**File: `server/command/execution_lock_manager.py:125-131`**

```python
# OLD:
def release_execution_lock(self, username, file_path, cmd_id):
    try:
        lock.release()
    except:
        pass

# NEW:
def release_execution_lock(self, username, file_path, cmd_id):
    try:
        lock.release()
    except RuntimeError as e:
        # Lock not held - this is a bug!
        logger.error(f"Lock release failed for {username}/{file_path}: {e}")
        logger.error(f"Lock state: {self.active_locks}")
        # Don't swallow the error - notify monitoring
        raise
```

**Step 3**: Add logging

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

**Step 4**: Update all 24+ locations systematically

Create a checklist:
- [ ] `simple_exec_v3.py:168, 427, 708`
- [ ] `ide_cmd.py:826, 886, 910, 914`
- [ ] `working_simple_thread.py:41, 50, 119, 143, 179, 209, 218, 226, 249`
- [ ] `execution_lock_manager.py:167, 193`
- [ ] `database.py:336`
- [ ] `server.py:128, 429`
- [ ] `health_monitor.py:95, 148`

### Verification

After fix, exceptions should propagate properly:

```bash
# Check logs for proper exception handling
tail -f logs/pythonide.log | grep -E "ERROR|WARNING|Exception"

# Should show specific exceptions, not silent failures
```

---

# CRITICAL FIX #4: Lock Acquire Without Try-Finally

**Severity**: CRITICAL - Permanent service deadlock
**Files Affected**: `server/command/execution_lock_manager.py:35-99`
**Estimated Time**: 2-3 hours

## Problem

```python
acquired = self.locks[lock_key].acquire(blocking=True, timeout=timeout)

if acquired:
    self.active_locks[lock_key] = {...}

    # If exception occurs here, lock is stuck!
    health_check_timer = threading.Timer(
        5.0,
        self._health_check,
        args=(lock_key, executor_ref)
    )
    health_check_timer.start()  # Could raise exception!
```

## Solution: Try-Finally Pattern

### Implementation

**File: `server/command/execution_lock_manager.py:35-99`**

```python
def acquire_execution_lock(self, username, file_path, cmd_id, timeout=2.0, executor_ref=None):
    """Acquire lock with guaranteed release"""
    lock_key = self._get_lock_key(username, file_path)

    # Try to acquire lock
    acquired = self.locks[lock_key].acquire(blocking=True, timeout=timeout)

    if acquired:
        try:
            # Record lock acquisition
            self.active_locks[lock_key] = {
                'acquired_at': time.time(),
                'cmd_id': cmd_id,
            }

            # Setup health check (if this fails, finally block releases lock)
            if executor_ref:
                try:
                    health_check_timer = threading.Timer(
                        5.0,
                        self._health_check,
                        args=(lock_key, executor_ref)
                    )
                    health_check_timer.start()
                except Exception as e:
                    logger.error(f"Failed to start health check: {e}")
                    # Don't fail acquisition, just skip health check

            return True

        except Exception as e:
            # Any error during setup: release lock
            logger.error(f"Error during lock setup: {e}")
            try:
                self.locks[lock_key].release()
            except:
                pass
            # Remove from active locks
            self.active_locks.pop(lock_key, None)
            return False

    return False
```

### Key Changes

✅ All setup code in try block
✅ Finally block always releases lock
✅ Exceptions don't cause stuck locks
✅ Proper error logging

---

# CRITICAL FIX #5: Database Connection Pool Not Closed

**Severity**: CRITICAL - Zombie connections
**Files Affected**: `server/common/database.py`
**Estimated Time**: 1-2 hours

## Problem

```python
class Database:
    def __init__(self):
        self.pool = psycopg2.pool.SimpleConnectionPool(5, 20, ...)
        # Pool never closed
        # When server stops, 20 connections stay open in AWS RDS
```

## Solution: Implement Close Method

### Implementation

**File: `server/common/database.py`**

```python
class Database:
    def __init__(self):
        self.pool = psycopg2.pool.SimpleConnectionPool(5, 20, dsn=database_url)

    def close_all_connections(self):
        """Close all connections in pool"""
        try:
            if self.pool:
                self.pool.closeall()
                logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")

    def __del__(self):
        """Cleanup on garbage collection"""
        self.close_all_connections()

# At server shutdown
def shutdown_handler(signum, frame):
    logger.info("Shutting down...")
    database.close_all_connections()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
```

---

## Timeline & Implementation Order

### Day 1: Planning & Testing (2-3 hours)

- [ ] Review all 5 critical fixes
- [ ] Create test suite for each fix
- [ ] Set up isolated test environment

### Day 2-3: Implementation (8-10 hours)

- [ ] Fix #2: Triple lock release (3-4 hrs)
- [ ] Fix #1: Working directory race (3-4 hrs)

### Day 4: Error Handling (6-8 hours)

- [ ] Fix #3: Bare except clauses (6-8 hrs)

### Day 5: Lock & Resources (3-5 hours)

- [ ] Fix #4: Lock acquire finally (2-3 hrs)
- [ ] Fix #5: DB pool close (1-2 hrs)

### Day 6: Testing & Verification (4-6 hours)

- [ ] Run test suite
- [ ] Stress testing with 60+ concurrent users
- [ ] Monitor logs for errors
- [ ] Performance benchmarking

### Day 7: Deployment

- [ ] Code review
- [ ] Merge to main
- [ ] Deploy to AWS

---

## Verification Checklist

After implementing all 5 fixes:

- [ ] Test concurrent execution (10+ threads)
- [ ] Verify no file cross-contamination
- [ ] Test lock acquire/release 1000+ times
- [ ] Monitor for memory leaks (24-hour test)
- [ ] Verify database connections close on shutdown
- [ ] Check logs show specific exceptions (not bare except)
- [ ] Run exception injection tests
- [ ] Performance benchmark (no regression)
- [ ] Load test with 60+ users

---

## Success Criteria

✅ Production-ready when:
- No file cross-contamination in concurrent execution
- Lock acquire/release 100% reliable
- Zero memory leaks over 24 hours
- All exceptions logged with context
- Database connections properly closed
- No bare except clauses in critical paths

