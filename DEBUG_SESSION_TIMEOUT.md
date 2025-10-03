# Session Timeout Debugging Guide

**Issue:** Users are getting logged out after 5-6 minutes instead of 1 hour
**Status:** 🔍 DEBUGGING MODE ACTIVE

---

## 🔍 Debug Logging Added

I've added comprehensive logging to track exactly what's happening with session timeouts.

### Where to Find Logs

**Local Development:**
```bash
# Server logs will show in terminal where you run server.py
python server/server.py
```

**AWS Production:**
```bash
# View ECS logs
aws logs tail /aws/ecs/pythonide --follow --region us-east-2 --filter-pattern "[SESSION-DEBUG]"

# Or via AWS Console:
# ECS > Clusters > pythonide-cluster > Tasks > View logs in CloudWatch
```

---

## 📊 What the Logs Will Show

### On Login (Session Creation):
```
[SESSION-CREATE] Creating session for user sa9082
[SESSION-CREATE] Current time: 2025-10-02 15:30:00 (type: <class 'datetime.datetime'>, tz: None)
[SESSION-CREATE] Expires at: 2025-10-03 15:30:00
[SESSION-CREATE] Initial last_activity: 2025-10-02 15:30:00
[SESSION-CREATE] Session created successfully for sa9082
```

### On Activity Update (Every WebSocket Message):
```
[ACTIVITY-UPDATE] Updating session activity to: 2025-10-02 15:35:00 (type: <class 'datetime.datetime'>, tz: None)
[ACTIVITY-UPDATE] Session activity updated successfully
```

### On Session Validation (Every Request):
```
[SESSION-DEBUG] User: sa9082
[SESSION-DEBUG] Current time: 2025-10-02 15:36:00 (type: <class 'datetime.datetime'>, tz: None)
[SESSION-DEBUG] Last activity raw: 2025-10-02 15:35:00 (type: <class 'datetime.datetime'>)
[SESSION-DEBUG] Already datetime: 2025-10-02 15:35:00 (tz: None)
[SESSION-DEBUG] Final last_activity: 2025-10-02 15:35:00 (tz: None)
[SESSION-DEBUG] Idle duration: 0:01:00 (seconds: 60.0)
[SESSION-DEBUG] Timeout threshold: 1:00:00 (seconds: 3600.0)
[SESSION-DEBUG] Will logout? False
```

### On Auto-Logout (If Triggered):
```
[SESSION-TIMEOUT] User sa9082 logged out due to inactivity
[SESSION-TIMEOUT] Idle duration: 1:05:23 > threshold: 1:00:00
[SESSION-TIMEOUT] Last activity was: 2025-10-02 14:30:00
```

---

## 🎯 What to Look For

### 1. **Timezone Issues**
Look for any timezone mismatches:
```
❌ BAD: tz: <UTC>  (timezone-aware)
✅ GOOD: tz: None   (timezone-naive)
```

If you see timezone-aware datetimes, the timezone stripping isn't working.

### 2. **Time Discrepancies**
Check if times are being stored/read differently:
```
Created: 2025-10-02 15:00:00
Read back: 2025-10-02 19:00:00  ❌ 4-hour difference!
```

This would indicate timezone conversion is happening in PostgreSQL.

### 3. **Idle Duration Calculation**
The math should be straightforward:
```
Current: 2025-10-02 15:06:00
Last: 2025-10-02 15:00:00
Idle: 0:06:00 (360 seconds) ✅ Correct
```

If you see something like:
```
Current: 2025-10-02 15:06:00
Last: 2025-10-02 15:00:00
Idle: 4:06:00 (14760 seconds) ❌ Wrong! Timezone issue
```

---

## 🔬 Step-by-Step Debugging Process

### Step 1: Test Login
1. Login to the IDE
2. Check server logs for `[SESSION-CREATE]` messages
3. **Verify:** Current time and last_activity should match
4. **Verify:** Both should have `tz: None`

### Step 2: Test Activity Updates
1. Type something in the IDE or run code
2. Check logs for `[ACTIVITY-UPDATE]` messages
3. **Verify:** Activity updates are happening
4. **Verify:** Times have `tz: None`

### Step 3: Wait 6 Minutes
1. Don't interact with IDE for exactly 6 minutes
2. Then type something or run code
3. Check logs for `[SESSION-DEBUG]` messages
4. **Look at:**
   - `Idle duration: X:XX:XX`
   - `Will logout? True/False`

### Step 4: Analyze the Logout
If you get logged out at 6 minutes:
- Check the `[SESSION-DEBUG]` logs just before logout
- Look at the idle duration calculation
- Compare `last_activity` raw value vs final value

---

## 🐛 Possible Root Causes

### Cause 1: PostgreSQL Timezone Conversion
**Symptom:** Times change when read from database
**Debug:** Compare `[SESSION-CREATE]` time vs `[SESSION-DEBUG]` Last activity raw

**Fix if found:**
```sql
-- Check PostgreSQL timezone setting
SHOW timezone;

-- If not UTC, the times might be getting converted
```

### Cause 2: psycopg2 Timezone Handling
**Symptom:** `last_activity` has timezone when read even though we stored naive datetime
**Debug:** Look at `Last activity raw` - does it have a timezone?

**Fix if found:**
```python
# In database.py, when creating connection pool
connect_args = {
    'timezone': None,  # Force naive datetime handling
}
```

### Cause 3: Background Cleanup Job
**Symptom:** No timeout in validate_session, but user still gets logged out
**Debug:** Search logs for `cleanup_idle_sessions`

**Fix if found:** The background job at line 608-660 might have wrong timeout

### Cause 4: Multiple validate_session Calls
**Symptom:** validate_session is called many times per minute
**Debug:** Count how many `[SESSION-DEBUG]` messages appear per minute

**Fix if found:** Reduce validation frequency or cache results

---

## 🔧 Quick Diagnostic Commands

### Check Database Session Table
```sql
-- Connect to PostgreSQL
psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com -U pythonide_admin -d pythonide

-- Check current sessions
SELECT username, last_activity,
       NOW() as current_time,
       NOW() - last_activity as idle_duration,
       EXTRACT(EPOCH FROM (NOW() - last_activity)) as idle_seconds
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE is_active = true;

-- Check PostgreSQL timezone
SHOW timezone;

-- Check data type of last_activity
SELECT column_name, data_type, datetime_precision
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'last_activity';
```

### Check Server Logs
```bash
# Local
tail -f server/pythonide.log | grep SESSION

# AWS
aws logs tail /aws/ecs/pythonide --follow --region us-east-2 --filter-pattern SESSION
```

---

## 📋 Information to Collect

When you test, please collect:

1. **Login logs** - Full `[SESSION-CREATE]` block
2. **Activity logs** - At least 2 `[ACTIVITY-UPDATE]` entries
3. **Validation logs** - At least 3 `[SESSION-DEBUG]` blocks (right after login, after 3 min, after 6 min)
4. **Timeout logs** - If logout happens, the `[SESSION-TIMEOUT]` block
5. **Database query** - Result of checking `last_activity` in database directly

---

## 🔄 Rollback Option (If Needed)

If debugging doesn't work out, I can provide a clean rollback that:
- ✅ Keeps single-session enforcement (this works)
- ❌ Removes auto-logout after inactivity
- 📝 Saves the timeout code for future debugging

Just let me know if you want the rollback!

---

## 📝 Next Steps

1. **Deploy this debug version** to your environment
2. **Login and test** following the debugging process above
3. **Share the logs** - I'll analyze them to find the exact issue
4. **Fix or rollback** based on findings

The debug logs will tell us EXACTLY what's going wrong!
