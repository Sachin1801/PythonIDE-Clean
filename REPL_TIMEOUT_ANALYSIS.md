# REPL Timeout Analysis: 1-Minute Console Timeout

**Date:** October 2, 2025
**Issue:** Proposal to add 1-minute timeout for REPL/console execution
**Objective:** Prevent infinite loops from consuming server resources

---

## 📊 Current Implementation

### How the Hybrid REPL System Works

**Architecture:**
1. **Script Execution** → **REPL Mode** (seamless transition)
2. Each file gets its own REPL session with variable persistence
3. REPL sessions managed by `REPLRegistry` (singleton pattern)
4. Sessions persist across WebSocket reconnections

**Key Components:**

#### 1. `HybridREPLThread` (hybrid_repl_thread.py)
- Runs Python subprocess for script + REPL
- **Current Timeouts:**
  - Script execution: `60 seconds` (EXECUTION_TIMEOUT env var, line 52)
  - REPL mode: `300 seconds` (5 minutes, line 58)
  - Timeout monitoring: **DISABLED** (line 469: `return` immediately)

#### 2. `REPLRegistry` (repl_registry.py)
- Manages REPL processes per user
- **Current Idle Timeout:** `3600 seconds` (60 minutes, line 55)
- Cleanup runs every 60 seconds (line 54)
- Max 2 processes per user (configurable)

#### 3. Process Flow
```
1. Student clicks "Run" on script.py
   ↓
2. HybridREPLThread created with script_path
   ↓
3. Wrapper script executes:
   a) Run user script
   b) If no errors, transition to REPL mode
   c) Signal REPL_MODE_START to frontend
   ↓
4. REPL loop starts (infinite while True loop, line 307)
   ↓
5. Student can interact indefinitely
   ↓
6. Session cleaned up after 60 minutes of NO activity
```

---

## 🎯 Your Proposed Change

**Add 1-minute active timeout for REPL:**
- REPL can run for maximum 1 minute **total** (not idle time)
- After 1 minute, automatically stop console
- Goal: Prevent infinite loops from running indefinitely

---

## ✅ Is This a Good Idea?

### **YES, but with caveats:**

**✅ Pros:**
1. **Resource Protection** - Prevents runaway processes from consuming CPU/memory
2. **Fair Usage** - Ensures no single student monopolizes server resources
3. **Educational Value** - Forces students to write efficient code
4. **Cost Control** - Reduces AWS ECS CPU costs (60+ students)
5. **Production Safety** - Prevents server crashes from infinite loops

**⚠️ Cons:**
1. **Legitimate Long Scripts** - Data processing, file operations, or complex algorithms may need >1 minute
2. **REPL Exploration** - Students lose ability to experiment interactively for extended periods
3. **Debugging Difficulty** - Hard to debug code that takes time to reproduce issues
4. **User Frustration** - Timeout during valid work feels punishing

---

## 🔍 What We Should Be Concerned About

### 1. **Timeout Type: Active vs Idle**

**Current Implementation:**
- ✅ Idle timeout: 60 minutes (if no user input, cleanup after 1 hour)
- ❌ Active timeout: DISABLED (monitoring function returns immediately)

**Your Proposal:**
- Active timeout: 1 minute total execution time

**Concern:** Active timeout is MORE disruptive than idle timeout.

**Example:**
```python
# Script that legitimately needs 2 minutes
import time
for i in range(100):
    print(f"Processing item {i}")
    time.sleep(1.2)  # 2 minutes total
```

With 1-minute active timeout, this would be killed even though it's valid work.

### 2. **Script vs REPL Timeout**

**Current Separate Limits:**
- Script execution: 60 seconds
- REPL mode: 300 seconds (5 minutes)

**Should timeout apply to:**
- ✅ **Script execution only** (prevents `while True` in student code)
- ⚠️ **REPL mode** (kills interactive exploration after 1 minute)

**Recommendation:** Keep script timeout at 60s, add 1-minute **per-command** timeout in REPL.

### 3. **Per-Command vs Total Session Timeout**

**Two different approaches:**

**Option A: Total Session Timeout (your proposal)**
```
Run script → REPL starts → 1 minute timer starts
Student types: x = 5
Student types: print(x * 2)
Student types: for i in range(100): print(i)
← After 1 minute total, REPL killed
```

**Option B: Per-Command Timeout (better for REPL)**
```
Run script → REPL starts
Student types: x = 5 ← 1-minute timer for THIS command
Student types: print(x * 2) ← Fresh 1-minute timer
Student types: while True: pass ← Killed after 1 minute
```

**Recommendation:** Use **per-command timeout** for REPL mode.

### 4. **User Experience (UX) Concerns**

**Current UX:**
- Student runs script → REPL opens → Can use indefinitely
- No warning about timeouts
- Session dies silently after 60 minutes of inactivity

**With 1-minute timeout:**
- Student runs script → REPL opens
- Student starts typing complex multi-line code
- TIMEOUT! (mid-work)
- Lost work, frustration

**Recommendation:** Add visible countdown timer + warning at 45 seconds.

### 5. **Infinite Loop Detection vs Timeout**

**Better Alternative:** Detect infinite loops instead of hard timeout.

**Smart Detection:**
```python
# Monitor CPU usage instead of time
if cpu_usage > 95% for 30 seconds:
    Send warning: "High CPU usage detected. Infinite loop?"
    Offer: [Keep Running] [Stop]

if cpu_usage > 95% for 60 seconds:
    Auto-kill with message: "Process stopped due to excessive CPU usage"
```

This allows:
- ✅ Long-running legitimate scripts (low CPU)
- ❌ Infinite loops (high CPU)

### 6. **AWS Cost vs Student Experience**

**Current AWS Setup:**
- ECS Fargate auto-scaling
- Scales based on CPU load > 45%
- 60+ concurrent students

**Cost Analysis:**
```
Scenario 1: No timeout (current)
- Student leaves infinite loop running
- 1 CPU core @ 100% for hours
- Cost: ~$0.10/hour/student = $6/hour worst case

Scenario 2: 1-minute timeout (your proposal)
- Infinite loop runs max 1 minute
- Cost: ~$0.002/student = $0.12/hour worst case
- Savings: $5.88/hour worst case
```

**But:**
- Students will re-run broken code multiple times
- Legitimate 2-minute scripts get killed → re-run → more CPU waste
- Frustration → more support requests → more professor time

**Recommendation:** Balance cost vs UX - use 2-3 minute timeout with warnings.

---

## 🏗️ Current Code Design

### Timeout Monitoring (Currently Disabled)

**File:** `server/command/hybrid_repl_thread.py`

**Lines 466-502:** `monitor_timeout()` method
```python
def monitor_timeout(self):
    """Monitor execution time and kill if exceeds limit"""
    # Disable timeout monitoring for now - it's interfering with input()
    # TODO: Implement smarter timeout that pauses during input wait
    return  # ← Currently exits immediately (line 470)

    # Only monitor during script execution, not REPL
    while self.alive and self.p and not self.repl_mode:
        elapsed = time.time() - self.start_time

        # Check if timeout exceeded
        if elapsed > self.cpu_time_limit + 5:
            print(f"[TIMEOUT] Process {self.cmd_id} exceeded time limit")
            self.response_to_client(1, {
                "stdout": f"\n[TIMEOUT] Execution time limit exceeded\n"
            })
            self.kill()
            break
```

**Why Disabled:**
- Interferes with `input()` prompts
- Would kill process while waiting for user input
- Needs "smart timeout" that pauses during interactive wait

### REPL Loop (Infinite by Design)

**Lines 306-382:** Interactive REPL loop
```python
# Interactive REPL loop with proper multiline support
while True:  # ← Infinite loop, by design
    try:
        prompt = ">>> "
        line = input(prompt)  # Blocks waiting for user

        # Execute code, handle multiline, etc.

    except SystemExit:
        break
    except KeyboardInterrupt:
        print("\\nKeyboardInterrupt")
    except EOFError:
        print()
        sys.exit(0)
```

**Current Behavior:**
- REPL runs indefinitely
- Only stops on: SystemExit, EOFError, or kill signal
- No timeout within REPL itself

### Cleanup (Idle Timeout)

**File:** `server/command/repl_registry.py`

**Lines 204-245:** Background cleanup thread
```python
def _cleanup_expired_processes(self):
    """Background thread to clean up expired REPL processes."""
    while True:
        time.sleep(self._cleanup_interval)  # 60 seconds

        # Clean up processes idle for > 60 minutes
        if current_time - last_access > timedelta(seconds=self._max_idle_time):
            expired_processes.append((username, file_path, "expired"))
```

**Current Behavior:**
- Checks every 60 seconds
- Kills REPLs idle for > 60 minutes (3600 seconds)
- Tracks `last_access` time updated on every user interaction

---

## 🔧 Changes Needed for 1-Minute Timeout

### Option A: Simple Active Timeout (Your Proposal)

**File:** `server/command/hybrid_repl_thread.py`

**Change 1:** Re-enable timeout monitoring for REPL
```python
# Line 466-502
def monitor_timeout(self):
    """Monitor execution time and kill if exceeds limit"""
    # REMOVED: return statement (line 470)

    # Monitor during BOTH script execution AND REPL mode
    while self.alive and self.p:  # Removed: and not self.repl_mode
        elapsed = time.time() - self.start_time

        # Check if timeout exceeded (1 minute = 60 seconds)
        timeout_limit = 60  # NEW: 1 minute for everything
        if elapsed > timeout_limit:
            print(f"[TIMEOUT] Process exceeded 1-minute limit")
            self.response_to_client(1, {
                "stdout": f"\n[TIMEOUT] Console stopped after 1 minute\n"
            })
            self.kill()
            break

        time.sleep(1)
```

**Change 2:** Update environment variable defaults
```python
# Line 52-58
self.cpu_time_limit = int(os.environ.get("EXECUTION_TIMEOUT", "60"))  # Script: 60s
self.repl_cpu_limit = 60  # Changed from 300 to 60 seconds (1 minute)
```

**Problem with Option A:**
- ❌ Kills REPL mid-work
- ❌ Timer doesn't pause during `input()` wait
- ❌ Students typing slowly get killed

---

### Option B: Per-Command Timeout (Better)

**Approach:** Monitor each REPL command separately, reset timer after each.

**Change 1:** Add per-command timeout in wrapper script
```python
# File: hybrid_repl_thread.py, line 306-382 (wrapper code)

# Replace the REPL loop with timeout-wrapped version:
import signal
import time

# Timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError("Command execution exceeded 1 minute")

# Interactive REPL loop with per-command timeout
while True:
    try:
        prompt = ">>> "
        line = input(prompt)

        # Set 60-second alarm for this command
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)  # 1 minute per command

        try:
            # Execute code (existing logic)
            # ...existing code...

            # Cancel alarm after successful execution
            signal.alarm(0)

        except TimeoutError as e:
            print(f"\\n[TIMEOUT] Command execution exceeded 1 minute")
            print("Please check for infinite loops or optimize your code")
            signal.alarm(0)  # Cancel alarm
            in_multiline = False
            multiline_buffer = []

    except SystemExit:
        break
    except KeyboardInterrupt:
        signal.alarm(0)  # Cancel alarm
        print("\\nKeyboardInterrupt")
```

**Problem with Option B:**
- ⚠️ More complex implementation
- ⚠️ `signal.alarm()` only works on Unix/Linux (not Windows local dev)
- ✅ Better UX: only kills long-running commands, not the REPL session

---

### Option C: CPU-Based Detection (Best)

**Approach:** Monitor CPU usage instead of elapsed time.

**File:** `server/command/hybrid_repl_thread.py`

**Change:** Add CPU monitoring in `monitor_timeout()`
```python
def monitor_timeout(self):
    """Monitor CPU usage and kill runaway processes"""
    high_cpu_start = None
    warning_sent = False

    while self.alive and self.p:
        try:
            if self.p and self.p.pid:
                process = psutil.Process(self.p.pid)
                cpu_percent = process.cpu_percent(interval=1.0)

                # Detect sustained high CPU (potential infinite loop)
                if cpu_percent > 90:
                    if high_cpu_start is None:
                        high_cpu_start = time.time()

                    high_cpu_duration = time.time() - high_cpu_start

                    # Warning after 30 seconds of high CPU
                    if high_cpu_duration > 30 and not warning_sent:
                        self.response_to_client(1, {
                            "stdout": "\n⚠️ [WARNING] High CPU usage detected. Possible infinite loop?\n"
                        })
                        warning_sent = True

                    # Kill after 60 seconds of sustained high CPU
                    if high_cpu_duration > 60:
                        self.response_to_client(1, {
                            "stdout": "\n[TIMEOUT] Process stopped due to excessive CPU usage (possible infinite loop)\n"
                        })
                        self.kill()
                        break
                else:
                    # Reset if CPU drops below threshold
                    high_cpu_start = None
                    warning_sent = False

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break

        time.sleep(1)
```

**Advantages:**
- ✅ Allows long-running LOW CPU tasks (file processing, sleeps, etc.)
- ✅ Catches infinite loops (high CPU)
- ✅ Better user experience
- ✅ More cost-effective (doesn't kill legitimate work)

---

## 🚨 Areas of Concern

### 1. **Local Development vs Production**

**Local (macOS/Windows):**
- `psutil` may behave differently
- `signal.alarm()` doesn't work on Windows
- Resource limits (`resource` module) only work on Unix

**Production (AWS ECS Linux):**
- `psutil` works correctly
- `signal.alarm()` works
- Resource limits work

**Testing Required:**
- ✅ Test timeout on local macOS
- ✅ Test timeout in Docker (Linux container)
- ✅ Test timeout on AWS ECS production

### 2. **Input() Blocking**

**Problem:** Timeout should NOT trigger while waiting for `input()`

**Current Code Comment (line 469):**
> "Disable timeout monitoring for now - it's interfering with input()"

**Solution:**
- Don't monitor timeout while in `input()` wait state
- Only monitor during actual code execution

**Detection:**
```python
# In wrapper, track input state
_in_input_wait = False

def _custom_input(prompt=""):
    global _in_input_wait
    _in_input_wait = True
    result = _original_input(prompt)
    _in_input_wait = False
    return result

# In monitor thread, check:
if not getattr(self, '_in_input_wait', False):
    # Only check timeout if not waiting for input
```

### 3. **Multi-Student Scenario**

**Current Capacity:** 60+ concurrent students

**Scenario 1: All students run infinite loops without timeout**
```
60 students × 1 CPU core each = 60 cores @ 100% = Server crash or huge AWS bill
```

**Scenario 2: With 1-minute timeout**
```
Student runs infinite loop → Killed after 60s → Re-runs → Killed again
60 students × re-running every minute = Still high load, but contained
```

**Scenario 3: With CPU-based detection**
```
Student runs infinite loop → CPU spikes → Warning at 30s → Killed at 60s
Student runs legitimate slow script → Low CPU → Runs to completion
Optimal resource usage
```

### 4. **REPL Session Persistence**

**Current:** REPL sessions persist across:
- WebSocket reconnections
- Tab switches
- Browser refresh (session ID maintained)

**With Active Timeout:**
- Student switches tabs → Returns 2 minutes later → Session dead
- Student gets disconnected → Reconnects → Session dead
- Poor UX for legitimate use cases

**Recommendation:** Use idle timeout (no activity), not active timeout (total time).

### 5. **Frontend UX**

**Current:** No visible indication of timeout limits

**Needed:**
1. **Countdown Timer** in console header
   - Shows: "Console active: 0:43 / 1:00"
   - Turns yellow at 0:45
   - Turns red at 0:50

2. **Warning Message**
   - At 45 seconds: "⚠️ Console will timeout in 15 seconds"
   - At 55 seconds: "⚠️ Console will timeout in 5 seconds"

3. **Post-Timeout Message**
   - "🛑 Console stopped after 1 minute to prevent infinite loops"
   - "Click 'Run' to restart with fresh timeout"

4. **Settings Option** (for professors)
   - "Extend timeout to 5 minutes for this session"
   - Admin override for demonstrations

### 6. **Error Handling & Recovery**

**Graceful Shutdown:**
```python
# Before killing process, try to save state
try:
    # Send SIGTERM first (graceful)
    self.p.terminate()
    self.p.wait(timeout=2)
except subprocess.TimeoutExpired:
    # Force kill if doesn't respond
    self.p.kill()
```

**Message to Student:**
```
🛑 Console Timeout

Your code has been running for 1 minute and was automatically stopped.

Possible reasons:
1. Infinite loop (e.g., while True without break)
2. Very slow operation
3. Waiting for input that never came

To fix:
✓ Check for infinite loops in your code
✓ Add loop counters and limits
✓ Optimize slow operations

[View Last 50 Lines of Output]  [Restart Console]
```

---

## 📋 Testing Checklist

### Pre-Deployment Testing (Local):

**Script Execution:**
- [ ] Run script < 60 seconds → Should complete
- [ ] Run script > 60 seconds → Should timeout
- [ ] Run script with input() → Should not timeout during wait
- [ ] Run script with infinite loop → Should timeout

**REPL Mode:**
- [ ] Open REPL → Type simple command → Should work
- [ ] Open REPL → Wait 2 minutes idle → Check if killed (should persist)
- [ ] Open REPL → Run long command (60s+) → Should timeout/complete based on implementation
- [ ] Open REPL → Run infinite loop → Should timeout

**Edge Cases:**
- [ ] Student runs script → Switches tab → Returns → REPL still active?
- [ ] Student runs script → Closes tab → Reopens → REPL gone?
- [ ] Multiple students run infinite loops simultaneously → All timeout?
- [ ] Professor (admin) account → Same timeout as students?

**Resource Monitoring:**
- [ ] Check CPU usage during infinite loop
- [ ] Check memory usage during infinite loop
- [ ] Verify process cleanup after timeout
- [ ] Check for zombie processes

### Production Testing (AWS):

**Gradual Rollout:**
1. [ ] Deploy to staging/test environment
2. [ ] Test with 5 test accounts
3. [ ] Monitor CloudWatch logs for timeout events
4. [ ] Check ECS CPU metrics
5. [ ] Deploy to production with 10% rollout
6. [ ] Monitor for 24 hours
7. [ ] Increase to 50% if stable
8. [ ] Full rollout after 48 hours

**Monitoring:**
- [ ] Set up CloudWatch alarm for high timeout rate
- [ ] Track average console runtime
- [ ] Monitor student support requests
- [ ] Check AWS costs (should decrease)

---

## 💡 Recommendations

### Best Implementation Strategy:

**Phase 1: Soft Launch (Week 1)**
1. ✅ Implement **CPU-based detection** (Option C)
2. ✅ Add warnings at 30 seconds high CPU
3. ✅ Kill at 60 seconds sustained high CPU
4. ✅ Keep idle timeout at 60 minutes
5. ✅ Add frontend countdown timer

**Phase 2: Monitor & Adjust (Week 2-3)**
1. Collect data on timeout frequency
2. Survey students: "Did timeout interrupt legitimate work?"
3. Analyze CloudWatch logs for patterns
4. Adjust thresholds based on data

**Phase 3: Optimize (Week 4+)**
1. Implement per-command timeout if needed
2. Add professor override settings
3. Create student dashboard showing resource usage
4. Fine-tune CPU thresholds

### Recommended Timeout Values:

| Scenario | Timeout | Reasoning |
|----------|---------|-----------|
| **Script execution** | 60 seconds (current) | Good for intro Python course |
| **REPL per-command** | 60 seconds | Prevents infinite loop in REPL |
| **REPL total session** | No limit | Allow interactive exploration |
| **Idle timeout** | 60 minutes (current) | Clean up forgotten sessions |
| **CPU-based kill** | 60s @ >90% CPU | Catches infinite loops only |

### Configuration (Environment Variables):

Add to `.env` and AWS ECS:
```bash
# Script execution timeout (default: 60 seconds)
EXECUTION_TIMEOUT=60

# REPL per-command timeout (default: 60 seconds)
REPL_COMMAND_TIMEOUT=60

# REPL idle timeout before cleanup (default: 3600 seconds = 60 minutes)
REPL_IDLE_TIMEOUT=3600

# CPU threshold for infinite loop detection (default: 90%)
CPU_THRESHOLD=90

# CPU high usage duration before kill (default: 60 seconds)
CPU_HIGH_DURATION_LIMIT=60
```

---

## 🎯 Final Answer to Your Questions

### Is 1-minute timeout a good idea?

**YES, with modifications:**
- ✅ Use 1-minute per-command timeout in REPL
- ✅ Use CPU-based detection for infinite loops
- ❌ Don't use 1-minute total session timeout (too disruptive)

### What should we be concerned about?

1. ✅ **Input blocking** - Don't timeout during input() wait
2. ✅ **Legitimate long scripts** - Use CPU detection, not time
3. ✅ **User experience** - Add warnings, countdown, clear messages
4. ✅ **Local vs production** - Test both environments thoroughly
5. ✅ **Multi-student load** - Monitor resource usage patterns

### How is code currently designed?

- ✅ Timeout monitoring exists but is **DISABLED**
- ✅ Only idle timeout (60 minutes) is active
- ✅ REPL loop runs indefinitely by design
- ✅ No per-command timeout in REPL

### What changes do we need?

**Minimal Safe Implementation:**
1. Re-enable `monitor_timeout()` with CPU monitoring
2. Add warning messages at 30s high CPU
3. Kill at 60s sustained high CPU
4. Add frontend countdown timer
5. Update environment variables

**Code changes:** ~100 lines (mostly in `hybrid_repl_thread.py`)

### Where could this cause problems?

**Local:**
- ⚠️ `psutil` might not be installed (add to requirements.txt)
- ⚠️ macOS resource limits behave differently
- ✅ Should work fine with CPU-based detection

**Production:**
- ✅ Should work perfectly (Linux + psutil available)
- ⚠️ Monitor for unexpected student complaints
- ⚠️ Watch CloudWatch for timeout patterns

---

## 🚀 Ready to Implement?

Let me know if you want me to:

1. **Option A:** Implement simple 1-minute active timeout (fast, but disruptive)
2. **Option B:** Implement per-command timeout (medium complexity, better UX)
3. **Option C:** Implement CPU-based detection (recommended, best balance)

I can make the code changes and test locally before deploying to production.

**My recommendation:** Start with **Option C (CPU-based)** for best UX and resource protection.
