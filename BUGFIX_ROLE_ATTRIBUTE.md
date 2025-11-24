# Bug Fix: AttributeError 'role' not found

## Error
```
AttributeError: 'SimpleExecutorV3' object has no attribute 'role'
  File "/app/server/command/simple_exec_v3.py", line 693, in execute_script
    SecurePath._role = self.role
```

## Root Cause
The `SimpleExecutorV3` class did not have a `role` attribute, but the security validation code (added in the security fix) was trying to access `self.role`.

## Files Modified

### 1. `/server/command/simple_exec_v3.py`

**Line 85-93**: Updated `__init__` method to accept `role` parameter
```python
# BEFORE:
def __init__(self, cmd_id: str, client, event_loop,
             script_path: Optional[str] = None, username: Optional[str] = None):
    ...
    self.username = username

# AFTER:
def __init__(self, cmd_id: str, client, event_loop,
             script_path: Optional[str] = None, username: Optional[str] = None, role: Optional[str] = None):
    ...
    self.username = username
    self.role = role or "student"  # Default to student if not provided
```

### 2. `/server/command/ide_cmd.py`

**Line 666**: Added role extraction from data
```python
username = data.get("username", "unknown")
role = data.get("role", "student")  # NEW LINE
```

**Line 692-699**: Updated SimpleExecutorV3 instantiation to pass role
```python
# BEFORE:
thread = SimpleExecutorV3(
    cmd_id,
    client,
    asyncio.get_event_loop(),
    script_path=file_path,
    username=username,
)

# AFTER:
thread = SimpleExecutorV3(
    cmd_id,
    client,
    asyncio.get_event_loop(),
    script_path=file_path,
    username=username,
    role=role,  # NEW LINE
)
```

**Line 787-788**: Updated empty REPL creation to pass role
```python
# BEFORE:
thread = SimpleExecutorV3(cmd_id, client, asyncio.get_event_loop(), script_path=None, username=username)

# AFTER:
role = data.get("role", "student")
thread = SimpleExecutorV3(cmd_id, client, asyncio.get_event_loop(), script_path=None, username=username, role=role)
```

## Verification

The `authenticated_ws_handler.py` already passes role in the data (line 563):
```python
actual_data["username"] = self.username
actual_data["role"] = self.role  # Already present
```

So the role flows like this:
1. User authenticates → `authenticated_ws_handler` stores `self.role`
2. User runs Python code → handler adds `role` to `data`
3. `ide_cmd.py` extracts `role` from `data`
4. `SimpleExecutorV3` receives and stores `role` as `self.role`
5. Security validation uses `self.role` to check permissions

## Status
✅ Fixed - The security fix will now work correctly with role-based permissions.

## Testing
Run the test script as student to verify:
- Student writes to read-only directories should be BLOCKED
- Professor writes should be ALLOWED
- No AttributeError should occur
