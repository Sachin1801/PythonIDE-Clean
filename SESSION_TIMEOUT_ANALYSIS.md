# Deep Analysis: Session Timeout Issue

**Created:** October 2, 2025
**Issue:** Users logged out after 5-6 minutes instead of 1 hour

---

## 🔍 Complete Code Flow Analysis

### 1. Session Creation (Login)
**File:** `auth/user_manager_postgres.py` lines 104-128

**Flow:**
```python
current_time = datetime.now()  # timezone-naive
expires_at = current_time + timedelta(hours=24)

INSERT INTO sessions (user_id, token, expires_at, last_activity)
VALUES (user_id, token, expires_at, current_time)
```

**Potential Issues:**
- ✅ current_time is timezone-naive (correct)
- ✅ last_activity is set explicitly
- ❓ How does PostgreSQL store this datetime?

---

### 2. Activity Updates (Every WebSocket Message)
**File:** `handlers/authenticated_ws_handler.py` lines 280, 291

**Triggered by:**
- Every authenticated WebSocket message (line 291)
- Every keepalive pong (line 280)

**Flow:**
```python
current_time = datetime.now()  # timezone-naive

UPDATE sessions SET last_activity = current_time
WHERE token = session_id AND is_active = true
```

**Frequency:** Every 30-60 seconds (due to keepalive pings)

**Potential Issues:**
- ✅ Updates are happening frequently
- ✅ Uses timezone-naive datetime.now()
- ❓ Does PostgreSQL convert this on storage?

---

### 3. Session Validation (On Every Request)
**File:** `auth/user_manager_postgres.py` lines 144-228

**When called:**
- WebSocket connection open (line 366 in authenticated_ws_handler.py)
- Possibly other API endpoints

**Flow:**
```python
# 1. Fetch session from database
SELECT s.*, u.username FROM sessions s JOIN users u
WHERE s.token = token AND s.is_active = true AND s.expires_at > NOW()

# 2. Get last_activity (this is the problem area)
last_activity = session.get("last_activity")

# 3. Calculate idle duration
idle_duration = datetime.now() - last_activity

# 4. Check if > 1 hour
if idle_duration > timedelta(hours=1):
    logout()
```

**Potential Issues:**
- ❓ What type/timezone is `last_activity` when read from PostgreSQL?
- ❓ Is the subtraction giving correct result?
- ❓ Is validation called too frequently?

---

## 🐛 Most Likely Root Causes

### Theory #1: PostgreSQL Timezone Conversion (90% probability)

**Scenario:**
```python
# We store
datetime.now() = 2025-10-02 15:00:00 (naive, Eastern Time)

# PostgreSQL might interpret this as UTC
# When read back, psycopg2 might add timezone
last_activity = 2025-10-02 15:00:00+00:00 (UTC)

# Then when we compare
current = 2025-10-02 15:06:00 (Eastern, naive)
last = 2025-10-02 15:00:00+00:00 (UTC, aware)

# Python sees this as
current (Eastern 3:06 PM) - last (UTC 3:00 PM = Eastern 11:00 AM)
= 4 hours 6 minutes ❌ WRONG!
```

**How to confirm:**
Look in debug logs for `Last activity raw` - if it has a timezone, this is the issue.

**Fix:**
```python
# In database.py connection config
connection_params = {
    'options': '-c timezone=UTC',  # Force specific timezone
}
```

---

### Theory #2: psycopg2 Returns Timezone-Aware Datetimes (80% probability)

**Scenario:**
Even though we store naive datetimes, psycopg2 might return them as timezone-aware based on server settings.

**How to confirm:**
Debug logs will show: `(type: <class 'datetime.datetime'>, tz: <DstTzInfo 'America/New_York'>)`

**Fix:**
```python
# After reading from database, always strip timezone
if hasattr(last_activity, 'tzinfo') and last_activity.tzinfo is not None:
    last_activity = last_activity.replace(tzinfo=None)
```

This is already in the code, but might not be working if the timezone is getting re-added somewhere.

---

### Theory #3: Server Timezone != User Timezone (50% probability)

**Scenario:**
```
Server (AWS): UTC timezone
User: Eastern Time (-4 hours from UTC)

Store: 15:00:00 (user's local time, but server thinks it's UTC)
Read: 15:00:00 (server interprets as UTC)
Current: 19:00:00 (server's UTC time)
Diff: 4 hours ❌
```

**How to confirm:**
Compare `[SESSION-CREATE] Current time` with your actual local time.

**Fix:**
Always use UTC everywhere:
```python
from datetime import timezone
current_time = datetime.now(timezone.utc).replace(tzinfo=None)
```

---

### Theory #4: Background Cleanup Job Interference (20% probability)

**File:** `auth/user_manager_postgres.py` lines 608-660, 677-698

**Scenario:**
The IdleSessionCleanupJob runs every 5 minutes and might have a bug.

**How to confirm:**
Search logs for "cleanup_idle_sessions" or "Terminated idle WebSocket"

**Fix:**
Disable the cleanup job temporarily (see rollback guide).

---

## 🔬 PostgreSQL Column Type Investigation

The `last_activity` column type is critical:

```sql
-- Check the exact data type
SELECT column_name, data_type, datetime_precision,
       column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'last_activity';
```

**Possible results:**
- `TIMESTAMP WITHOUT TIME ZONE` ✅ Good - stores as-is, no conversion
- `TIMESTAMP WITH TIME ZONE` ❌ Bad - PostgreSQL converts to UTC
- `TIMESTAMP` ❓ Ambiguous - depends on server settings

---

## 📊 Validation Frequency Analysis

**Current setup:**
- `update_session_activity()` called every ~45 seconds (keepalive ping)
- `validate_session()` called on:
  - WebSocket open (once per connection)
  - Possibly on every HTTP request

**This should be fine** - updates are more frequent than validation.

But if `validate_session()` is called on EVERY WebSocket message (not just on open), that could cause performance issues and make the bug more noticeable.

---

## 🎯 Debugging Strategy

### Phase 1: Deploy Debug Logging (DONE)
✅ Added comprehensive logging to all session methods

### Phase 2: Collect Logs (NEXT)
Test the system and collect:
1. Login logs - verify initial timestamp
2. Activity update logs - verify updates happen
3. Validation logs - see the exact calculation
4. Timeout logs - if logout happens, see why

### Phase 3: Analyze Logs
Look for:
- Timezone mismatches
- Time discrepancies
- Incorrect idle duration calculations

### Phase 4: Fix or Rollback
- If issue is clear: Apply targeted fix
- If issue is unclear: Rollback and debug offline

---

## 💡 Recommended Next Steps

**Option A: Debug First (Recommended if you can tolerate the issue for 1-2 days)**
1. Deploy the debug logging version
2. Have a few users test it
3. Collect and analyze logs
4. Apply targeted fix
5. Re-enable with confidence

**Option B: Rollback Now (Recommended if users are frustrated)**
1. Apply the rollback (removes auto-logout, keeps single-session)
2. Deploy debug logging in background
3. Collect logs from normal usage
4. Fix offline
5. Re-enable when ready

---

## 🔧 Quick Fixes to Try (If You Want)

### Fix #1: Force UTC Everywhere
```python
# In user_manager_postgres.py, replace all datetime.now() with:
from datetime import timezone
datetime.now(timezone.utc).replace(tzinfo=None)
```

### Fix #2: Check PostgreSQL Timezone Setting
```sql
-- On database
SHOW timezone;

-- If not 'UTC', change it
ALTER DATABASE pythonide SET timezone TO 'UTC';
```

### Fix #3: Use Unix Timestamps Instead
```python
# Store as integer (seconds since epoch)
import time
last_activity = int(time.time())

# Compare
idle_seconds = time.time() - last_activity
if idle_seconds > 3600:  # 1 hour
    logout()
```

This eliminates ALL timezone issues.

---

## 📝 Summary

**Most Likely Cause:** PostgreSQL timezone conversion

**Certainty:** 80%

**Best Next Step:** Deploy debug logging and collect data OR apply rollback

**Long-term Fix:** Switch to UTC timestamps or Unix epoch time

Let me know which approach you prefer!
