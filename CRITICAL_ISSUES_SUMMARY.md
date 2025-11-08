# CRITICAL ISSUES - Quick Reference

## Issue #1: Working Directory Race Condition 🔴

**Files**: `simple_exec_v3.py:346-349`
**Status**: CONFIRMED - Code verified

```
Thread 1: os.getcwd() → "/app/server"
Thread 2: os.getcwd() → "/mnt/efs/pythonide-data/Local/student1" ❌ WRONG!
Thread 1: os.chdir(original_cwd) → changes to student1's dir ❌ DATA CORRUPTION
```

**Risk**: With 60+ concurrent users, students' files created in wrong directories

---

## Issue #2: Triple Lock Release Paths 🔴

**Files**:
- `simple_exec_v3.py:237-241` (Path 1: After script)
- `simple_exec_v3.py:564-568` (Path 2: On stop)
- `simple_exec_v3.py:768-772` (Path 3: On cleanup)

**Status**: CONFIRMED - 3 release paths found

```
Execution: script completes → release lock
Meanwhile: stop signal arrives → release lock (AGAIN!)
Result: RuntimeError or corrupted state
```

---

## Issue #3: Bare Except Clauses 🔴

**Count**: 24+ instances found across codebase

**Locations**:
- `simple_exec_v3.py`: Lines 168, 427, 708
- `ide_cmd.py`: Lines 826, 886, 910, 914
- `working_simple_thread.py`: Lines 41, 50, 119, 143, 179, 209, 218, 226, 249
- `execution_lock_manager.py`: Lines 167, 193
- `common/database.py`: Line 336
- `server.py`: Lines 128, 429
- `health_monitor.py`: Lines 95, 148

**Status**: CONFIRMED - All found and logged

```python
try:
    os.chdir(script_dir)  # If this fails...
except:
    pass  # Error hidden! Lock never released!
```

---

## Issue #4: Lock Acquire Without Try-Finally 🔴

**File**: `execution_lock_manager.py:35-99`
**Status**: CONFIRMED

```python
acquired = self.locks[lock_key].acquire(blocking=True, timeout=timeout)

if acquired:
    # ... setup code ...
    # If exception occurs here, lock acquired but never released!
    health_check_timer = threading.Timer(...)
    health_check_timer.start()  # Could fail!
```

**Risk**: Lock held forever, service becomes unresponsive

---

## Issue #5: Rate Limiter Memory Leak 🟠

**File**: `server/common/rate_limiter.py`
**Status**: CONFIRMED

```python
self.request_timestamps[client_id].append(now)
# Keeps growing indefinitely
# After 1 day: 60 users × 86,400 requests = 5.184M timestamps in memory
```

---

## Verification Results

| Issue | Type | Count | Severity | Confirmed |
|-------|------|-------|----------|-----------|
| os.chdir() race | Architecture | 3 calls | CRITICAL | ✅ |
| Lock release paths | Locking | 3 paths | CRITICAL | ✅ |
| Bare except clauses | Error handling | 24+ | CRITICAL | ✅ |
| Lock acquire no finally | Locking | 1 | CRITICAL | ✅ |
| Memory leaks | Resources | 3 | HIGH | ✅ |
| Path traversal | Security | 2 | HIGH | ✅ |
| Thread safety | Threading | 3 | HIGH | ✅ |

---

## Immediate Actions Required

### 1. Replace os.chdir() (HIGH PRIORITY)

**Current Code** (UNSAFE):
```python
original_cwd = os.getcwd()
os.chdir(script_dir)
try:
    exec(compiled_code, self.namespace)
finally:
    os.chdir(original_cwd)
```

**Better Approach** (SAFE):
```python
# Option A: Use absolute paths
with open(os.path.join(script_dir, 'file.csv'), 'w') as f:
    # No chdir needed!

# Option B: Use subprocess with cwd
result = subprocess.run(
    ['python', script_path],
    cwd=script_dir,  # Thread-safe!
    capture_output=True
)

# Option C: Thread-local storage
import threading
_thread_local = threading.local()
```

### 2. Fix Lock Management (HIGH PRIORITY)

**Current Code** (UNSAFE):
```python
acquired = lock.acquire()
if acquired:
    # Risk: exception here → lock stuck
    setup_health_check()
```

**Better Code** (SAFE):
```python
lock.acquire()
try:
    setup_health_check()
finally:
    lock.release()  # Always releases
```

### 3. Replace Bare Except (HIGH PRIORITY)

**Current Code** (UNSAFE):
```python
try:
    os.chdir(script_dir)
except:  # Catches SystemExit, KeyboardInterrupt, everything!
    pass
```

**Better Code** (SAFE):
```python
try:
    os.chdir(script_dir)
except (OSError, IOError) as e:  # Specific exceptions only
    logger.error(f"Failed to change directory: {e}")
    raise
```

---

## Risk Assessment

### If Fixed This Week
- ✅ Production-ready for 60+ users
- ✅ Data integrity guaranteed
- ✅ No service outages
- ✅ Stable performance

### If Not Fixed
- ❌ Data corruption likely within days
- ❌ Random service outages
- ❌ Difficult debugging
- ❌ Unpredictable behavior
- ❌ Cannot scale beyond test environment

---

## Code Snippets for Quick Reference

### Affected Files (Priority Order)

1. **`server/command/simple_exec_v3.py`** - CRITICAL
   - Lines 346-349: os.chdir() calls
   - Lines 237-241: Lock release path 1
   - Lines 564-568: Lock release path 2
   - Lines 768-772: Lock release path 3
   - Lines 168, 427, 708: Bare except clauses

2. **`server/command/execution_lock_manager.py`** - CRITICAL
   - Lines 35-99: Lock acquire without finally
   - Lines 104-130: Lock release implementation
   - Lines 167, 193: Bare except clauses

3. **`server/command/ide_cmd.py`** - HIGH
   - Lines 826, 886, 910, 914: Bare except clauses
   - Line 730: Lock release call

4. **`server/command/working_simple_thread.py`** - HIGH
   - Lines 41, 50, 119, 143, 179, 209, 218, 226, 249: Bare except clauses

5. **`server/common/rate_limiter.py`** - HIGH
   - Memory leak accumulation

---

## Testing Checklist

After fixes, verify:

- [ ] Run 10 concurrent scripts, verify files created in correct directories
- [ ] Kill scripts at random times, verify locks release
- [ ] Rapidly acquire/release 100s of locks, verify no deadlock
- [ ] Monitor RAM for 24 hours with normal usage
- [ ] Run path traversal tests
- [ ] Verify WebSocket communication still works
- [ ] Check REPL transitions work correctly
- [ ] Verify exception handling via logs

