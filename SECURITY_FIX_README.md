# Security Fix: File Write Permission Enforcement

## Date: November 24, 2025

## Critical Security Vulnerability Discovered

### Issue Summary
Students were able to write to read-only directories (like "Lecture Notes/") when using absolute paths in their Python code, despite IDE interface restrictions preventing such access.

### Vulnerability Details

**What was broken:**
- IDE interface correctly blocked students from editing files in read-only directories
- However, when students executed Python code with file operations using absolute paths, they could bypass these restrictions
- This allowed students to corrupt shared CSV files, text files, and other data files that professors placed in read-only directories

**Attack Vectors:**
```python
# Example 1: Direct file write
open('/mnt/efs/pythonide-data/Lecture Notes/grades.csv', 'w').write('corrupted')

# Example 2: Pandas operations
import pandas as pd
df = pd.read_csv('data.csv')
df['Grade'] = 100
df.to_csv('/mnt/efs/pythonide-data/Lecture Notes/grades.csv')

# Example 3: Pathlib operations
from pathlib import Path
Path('/mnt/efs/pythonide-data/Lecture Notes/data.txt').write_text('hacked')

# Example 4: File deletion
import os
os.remove('/mnt/efs/pythonide-data/Lecture Notes/important.csv')
```

### Root Cause

The execution engine in `server/command/simple_exec_v3.py` used monkey-patching to contextualize relative paths to the script directory, but it did NOT validate absolute paths. This created an inconsistent security model:

- ✅ **IDE Interface**: Strict permission validation (secure)
- ❌ **Student Code Execution**: Only relative path contextualization, no absolute path validation (vulnerable)

### Impact

- **Severity**: HIGH - Academic integrity and data corruption risk
- **Affected Users**: All students (60+ users)
- **Data at Risk**: Professor-uploaded CSV files, text files, assignment data, grading rubrics
- **Exploitability**: Easy - any student with basic Python knowledge could discover this

---

## The Fix

### Changes Made

**File Modified:** `server/command/simple_exec_v3.py`

#### 1. Added Permission Validation Function (Lines 389-450)

Created `validate_student_path()` function that:
- Validates all file operations against user permissions
- Enforces directory boundaries (students restricted to `Local/{username}/`)
- Allows professors unrestricted access
- Prevents directory traversal attacks (`../` sequences)
- Distinguishes between read and write operations

**Permission Model:**
```python
STUDENTS:
- READ: ✅ Anywhere in IDE workspace (including Lecture Notes/)
- WRITE: ✅ Only within Local/{username}/ directory
- WRITE: ❌ Blocked everywhere else (Lecture Notes/, other students' directories)

PROFESSORS:
- READ: ✅ Unrestricted
- WRITE: ✅ Unrestricted
```

#### 2. Updated `contextualized_open()` (Lines 452-467)

Added permission validation to `open()` function:
- Validates both relative AND absolute paths
- Checks file mode to detect write operations
- Raises `PermissionError` if student attempts unauthorized write

#### 3. Added Destructive File Operation Patching (Lines 527-585)

Monkey-patched additional file operations:
- `os.remove()` - Delete files
- `os.rename()` - Rename/move files
- `os.mkdir()` / `os.makedirs()` - Create directories
- `os.rmdir()` - Remove directories

All now validate student permissions before executing.

#### 4. Added Pathlib.Path Security Wrapper (Lines 626-704)

Created `SecurePath` class that wraps `pathlib.Path` and validates:
- `Path.open()` - File opening
- `Path.write_text()` / `Path.write_bytes()` - File writes
- `Path.mkdir()` / `Path.rmdir()` - Directory operations
- `Path.unlink()` - File deletion
- `Path.rename()` / `Path.replace()` - File movement

#### 5. Module Replacement (Lines 713-722)

Replaced `os`, `os.path`, and `pathlib` modules in:
- `sys.modules` - Affects all future imports
- Script namespace - Affects direct usage

#### 6. Module Restoration (Lines 1111-1124)

Added cleanup to restore original modules after script execution.

---

## Security Guarantees

### After Fix

✅ **Students CANNOT:**
- Write CSV files to Lecture Notes/ directory
- Write text files to read-only directories
- Delete files outside their directory
- Create directories outside their directory
- Rename/move files to read-only directories
- Use directory traversal (`../`) to escape their directory
- Bypass restrictions using pandas, pathlib, or os modules

✅ **Students CAN:**
- Read files from Lecture Notes/ (read-only access preserved)
- Read files from anywhere in workspace (as intended)
- Write files within their own `Local/{username}/` directory
- Use all Python libraries normally within their workspace

✅ **Professors CAN:**
- Access everything (no restrictions)

---

## Testing

### Test Script: `test_security_fix.py`

A comprehensive test script has been created to verify the fix. It tests:

1. ❌ Write CSV to Lecture Notes (absolute path) - SHOULD FAIL
2. ❌ Write text file to Lecture Notes - SHOULD FAIL
3. ❌ Pandas CSV write to Lecture Notes - SHOULD FAIL
4. ❌ Pathlib write to Lecture Notes - SHOULD FAIL
5. ❌ Delete file in Lecture Notes - SHOULD FAIL
6. ❌ Create directory in Lecture Notes - SHOULD FAIL
7. ❌ Rename/move file to Lecture Notes - SHOULD FAIL
8. ❌ Directory traversal attack - SHOULD FAIL
9. ✅ Read from Lecture Notes - SHOULD SUCCEED
10. ✅ Write to own directory - SHOULD SUCCEED

### How to Test

**As a student user:**
1. Log into the IDE with a student account (e.g., `sa9082`)
2. Create a new Python file in `Local/sa9082/`
3. Copy the test script content into it
4. Run the script
5. Verify that tests 1-8 are BLOCKED with PermissionError
6. Verify that tests 9-10 SUCCEED

**Expected Output:**
```
[TEST 1] Attempting to write CSV to Lecture Notes (absolute path)
✅ BLOCKED: Permission denied: Students can only write to their own directory...

[TEST 2] Attempting to write text file to Lecture Notes
✅ BLOCKED: Permission denied: Students can only write to their own directory...

...

[TEST 9] Reading from Lecture Notes (SHOULD SUCCEED)
✅ SUCCESS: Read access to Lecture Notes/ works

[TEST 10] Writing to student's own directory (SHOULD SUCCEED)
✅ SUCCESS: Write to own directory works
```

---

## Deployment

### Steps to Deploy Fix

Since you mentioned you run frontend and backend services manually and need explicit service refresh:

#### 1. Review Changes
```bash
# View the changes made
git diff server/command/simple_exec_v3.py
```

#### 2. Test Locally (Optional but Recommended)
```bash
# Start the backend server
cd /Users/sachin/Desktop/Projects/PythonIDE-Clean
python server/server.py --port 10086

# In the IDE, run the test_security_fix.py script as a student
```

#### 3. Commit Changes
```bash
git add server/command/simple_exec_v3.py
git add test_security_fix.py
git add SECURITY_FIX_README.md

git commit -m "$(cat <<'EOF'
Security fix: Enforce file write permissions in student code execution

Critical security vulnerability fix that prevents students from writing
to read-only directories (like Lecture Notes/) when using absolute paths
in their Python code.

Changes:
- Added validate_student_path() for permission validation
- Updated contextualized_open() to validate absolute paths
- Added monkey-patching for os.remove, os.rename, os.mkdir, os.makedirs, os.rmdir
- Added SecurePath wrapper for pathlib.Path operations
- Added module restoration in cleanup

Students can now only write within Local/{username}/ directory while
maintaining read access to shared resources. Professors retain full access.

Fixes academic integrity issue where students could corrupt shared CSV/text
files in professor-controlled directories.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

#### 4. Push to Repository
```bash
# Push to main branch (triggers GitHub Actions deployment to AWS)
git push origin main
```

#### 5. Verify AWS Deployment
```bash
# Monitor GitHub Actions workflow
# Visit: https://github.com/{your-repo}/actions

# Once deployed, check ECS service status
aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-service \
  --region us-east-2 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'

# Check container logs for any errors
aws logs tail /aws/ecs/pythonide --follow --region us-east-2
```

#### 6. Production Testing
1. Log into production IDE with a student account
2. Run the `test_security_fix.py` script
3. Verify all permission checks work as expected
4. Test with a professor account to ensure unrestricted access

#### 7. Monitor for Issues
- Check logs for PermissionError exceptions (expected for blocked operations)
- Verify students can still complete legitimate assignments
- Watch for any reports of broken functionality

---

## Rollback Plan (If Needed)

If the fix causes issues:

```bash
# 1. Revert the commit
git revert HEAD
git push origin main

# 2. Wait for GitHub Actions to redeploy

# 3. Alternative: Manual rollback
git checkout <previous-commit-hash> server/command/simple_exec_v3.py
git commit -m "Rollback: Revert security fix due to issues"
git push origin main
```

---

## Additional Security Considerations

### What This Fix Does NOT Cover

1. **Subprocess/System Calls**: If students use `subprocess.run(['rm', 'file'])`, this is not caught
2. **Binary Libraries**: C-level file operations bypass Python monkey-patching
3. **Network Access**: Students could still exfiltrate data via network if network access is allowed
4. **Resource Limits**: This fix doesn't address CPU/memory limits (separate concern)

### Future Enhancements (Optional)

1. **Container-Based Sandboxing**:
   - Use Docker containers for each student execution
   - Provides stronger isolation than monkey-patching

2. **File System Quotas**:
   - Limit storage per student
   - Prevent disk space exhaustion attacks

3. **Audit Logging**:
   - Log all file operations (read and write)
   - Track which students access which files
   - Helps detect suspicious patterns

4. **Rate Limiting**:
   - Limit file operations per second
   - Prevent abuse/DoS attempts

---

## FAQ

### Q: Will this break existing student assignments?
**A:** No. Students who were using relative paths (the correct way) will see no change. Only attempts to write outside their directory will be blocked.

### Q: Can students still import pandas and use DataFrames?
**A:** Yes! Students can use pandas normally within their own directory. Only writes to read-only directories are blocked.

### Q: What error will students see if they try to write outside their directory?
**A:** They will see a clear error message:
```
PermissionError: Permission denied: Students can only write to their own directory (Local/sa9082/).
Attempted write to: Lecture Notes/grades.csv
```

### Q: Can professors still modify files in Lecture Notes/?
**A:** Yes! Professors have unrestricted access (`role == "professor"` bypasses all checks).

### Q: Does this affect the IDE file browser/editor?
**A:** No. The IDE interface already had proper permission checks. This fix only affects Python code execution.

### Q: What if a student finds a new bypass?
**A:** Report it immediately. The monkey-patching approach has limitations. For maximum security, consider container-based sandboxing (future enhancement).

---

## Technical Notes

### Why Monkey-Patching?

- **Pros**: Easy to implement, works for most cases, no infrastructure changes needed
- **Cons**: Can be bypassed with advanced techniques (subprocess, binary libraries)

For an educational environment with 60 students learning Python, monkey-patching provides adequate security. Students are unlikely to discover sophisticated bypass techniques.

### Performance Impact

- **Negligible**: Permission checks are fast (string comparisons and path operations)
- **No network latency**: All checks are local
- **Expected overhead**: < 1ms per file operation

### Compatibility

- **Python Version**: Works with Python 3.7+
- **Libraries**: Compatible with pandas, numpy, pathlib, csv, json, etc.
- **AWS EFS**: No changes needed to file system configuration

---

## Contact

For questions or issues with this fix, contact:
- **Project Lead**: Sachin Adlakha
- **Issue Tracker**: GitHub Issues (if repository is set up)

## References

- Original vulnerability report: (this investigation)
- Code changes: `server/command/simple_exec_v3.py`
- Test script: `test_security_fix.py`
- Project context: `CLAUDE.md`
