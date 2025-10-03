# Rollback Auto-Logout (Keep Single-Session)

**Purpose:** Remove auto-logout after inactivity while keeping single-session enforcement

---

## 🎯 What This Rollback Does

### ✅ Keeps (Working Features):
- Single-session enforcement (only 1 active session per user)
- Session activity tracking
- Session token validation
- WebSocket authentication
- Database-level session invalidation

### ❌ Removes (Problematic Feature):
- Auto-logout after 1 hour of inactivity
- Idle duration checking
- Background cleanup job for idle sessions

---

## 📝 Files to Modify

### 1. `server/auth/user_manager_postgres.py`

**Changes in `validate_session()` method (lines 170-216):**

Remove the entire auto-logout block and replace with just session validation.

**Before (lines 170-216):**
```python
# AUTO-LOGOUT: Check for 1-hour inactivity timeout
last_activity = session.get("last_activity")
# ... all the timeout logic ...
if idle_duration > INACTIVITY_TIMEOUT:
    self.logout(token)
    return None
```

**After:**
```python
# Auto-logout temporarily disabled for debugging
# Single-session enforcement still active (see line 89-102)
# Activity tracking still active (update_session_activity still called)
```

**Changes in `cleanup_idle_sessions()` method (lines 608-660):**

Make this method a no-op (do nothing).

**Before:**
```python
def cleanup_idle_sessions(self):
    # ... cleanup logic ...
```

**After:**
```python
def cleanup_idle_sessions(self):
    """
    Cleanup idle sessions - TEMPORARILY DISABLED
    Returns empty list to keep IdleSessionCleanupJob happy
    """
    return []  # No users to cleanup
```

---

## 🔧 Rollback Script

Here's the exact code to apply:

### File: `server/auth/user_manager_postgres.py`

**1. Replace lines 170-216 with:**
```python
            # AUTO-LOGOUT: TEMPORARILY DISABLED FOR DEBUGGING
            # Single-session enforcement is still active (working correctly)
            # Activity tracking is still active (update_session_activity still called)
            #
            # The inactivity timeout logic has been disabled because users were
            # getting logged out prematurely (5-6 minutes instead of 1 hour).
            #
            # To re-enable auto-logout after debugging:
            # 1. Review DEBUG_SESSION_TIMEOUT.md for debugging steps
            # 2. Collect logs to identify the root cause
            # 3. Fix the timezone/timing issue
            # 4. Restore the timeout logic from git history

            # For now, just validate the session exists and is active
            # (expires_at is still checked at line 152)
```

**2. Replace the `cleanup_idle_sessions()` method (lines 608-660) with:**
```python
    def cleanup_idle_sessions(self):
        """
        Cleanup sessions that have been idle for more than 1 hour.
        TEMPORARILY DISABLED - Returns empty list.

        This is called periodically by background job but does nothing
        until the auto-logout timeout issue is debugged and fixed.

        To re-enable:
        1. Debug the timeout calculation issue
        2. Restore original code from git history (commit before rollback)
        3. Test thoroughly before deploying
        """
        logger.info("Idle session cleanup temporarily disabled (rollback)")
        return []  # No users to cleanup
```

---

## 🚀 How to Apply Rollback

### Option 1: Manual Edit (Recommended)
1. Open `server/auth/user_manager_postgres.py`
2. Find line 170 (start of auto-logout block)
3. Replace lines 170-216 with the code above
4. Find the `cleanup_idle_sessions()` method
5. Replace with the disabled version above
6. Save and deploy

### Option 2: Use Git
```bash
# If you want to revert the entire auto-logout feature
git log --oneline | grep -i "timeout\|logout\|activity"

# Find the commit before auto-logout was added
# Then revert just those changes

# Or create a new branch with rollback
git checkout -b rollback/disable-auto-logout
# Make changes
git commit -m "Rollback: Disable auto-logout, keep single-session"
```

---

## ✅ What Will Still Work After Rollback

### 1. Single-Session Enforcement ✅
**Location:** `user_manager_postgres.py` lines 89-102

Users can only have 1 active session. If they login from a new location, the old session is invalidated.

**Test:**
1. Login from Browser A
2. Login from Browser B with same user
3. Browser A session should be terminated

### 2. Session Activity Tracking ✅
**Location:** `user_manager_postgres.py` lines 230-255

The `last_activity` column is still updated on every WebSocket message.

**Why keep it:**
- Ready for when auto-logout is fixed
- Can be used for analytics
- Doesn't hurt anything

### 3. Session Expiration (24 hours) ✅
**Location:** `user_manager_postgres.py` line 152

Sessions still expire after 24 hours (based on `expires_at` column).

**Test:**
- Login and note the time
- Session will expire 24 hours later
- User will need to login again

### 4. WebSocket Authentication ✅
**Location:** All WebSocket handlers

All WebSocket connections still require authentication.

---

## ❌ What Will Stop Working After Rollback

### 1. Auto-Logout After Inactivity ❌
Users will NOT be logged out if they're inactive for more than 1 hour.

**Impact:**
- Sessions can stay active for up to 24 hours
- Users need to manually logout
- Shared computers: users should click "Logout" button

### 2. Idle Session Cleanup Job ❌
The background job still runs but does nothing.

**Impact:**
- Minimal - it's just an empty loop
- Can be fully disabled if needed

---

## 🔍 After Rollback: How to Debug

1. **Deploy the debug logging version** (already added in this session)
2. **Test and collect logs** following `DEBUG_SESSION_TIMEOUT.md`
3. **Analyze logs** to find the timing issue
4. **Fix the root cause**
5. **Re-enable auto-logout** by restoring the code

---

## 📊 Comparison

| Feature | With Auto-Logout | After Rollback |
|---------|------------------|----------------|
| Single-session enforcement | ✅ Works | ✅ Works |
| Activity tracking | ✅ Works | ✅ Works |
| Auto-logout (1hr idle) | ❌ Buggy (5-6min) | ⏸️ Disabled |
| Session expiration (24hr) | ✅ Works | ✅ Works |
| WebSocket auth | ✅ Works | ✅ Works |
| User experience | 😞 Frustrating | 😊 Better |

---

## 🎯 Recommendation

**I recommend:**

1. **Apply the rollback now** - Improve user experience immediately
2. **Deploy debug logging** - So we can collect data in background
3. **Collect logs over next few days** - From real usage
4. **Analyze and fix** - Find the root cause
5. **Re-enable auto-logout** - Once properly debugged

This way:
- ✅ Users aren't frustrated
- ✅ Single-session still works
- ✅ We can debug properly
- ✅ Fix can be tested before re-deployment

---

## 🚨 If You Want to Apply This Rollback

Just say "Apply rollback" and I'll make the code changes immediately!
