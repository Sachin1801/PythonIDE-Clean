# Production Deployment Checklist - Staging → Main

**Date**: 2025-11-04
**Features**: Password Reset + Lecture_Examples Folder + WebSocket Cleanup
**Status**: Ready for Production Deployment

---

## 📋 Pre-Deployment Summary

### Changes Included:
1. ✅ **Student Password Change** - Re-enabled in Profile modal
2. ✅ **Admin Password Manager** - Route guard (only `admin_editor`)
3. ✅ **Lecture_Examples Folder** - Added to all student directories
4. ✅ **WebSocket Cleanup** - Verified (no hanging connections)

### Files Changed:
| File | Purpose |
|------|---------|
| `src/components/element/UserProfileModal.vue` | Re-enabled password change tab |
| `src/router/index.js` | Added admin route authentication |
| `server/common/file_storage.py` | Added Lecture_Examples folder creation |
| `server/auto_init_users.py` | Added Lecture_Examples for new users |
| `server/migrations/add_examples_folder.py` | Migration script for existing users |

---

## 🚀 Deployment Steps

### **Phase 1: Code Deployment (5-10 minutes)**

#### Step 1.1: Build Frontend
```bash
cd /home/sachinadlakha/on-campus/PythonIDE-Clean
npm run build
```

**Expected Output**:
```
✓ built in 2m 15s
```

#### Step 1.2: Create Pull Request (GitHub)
```bash
# Push staging branch to GitHub
git checkout staging
git add .
git commit -m "feat: Add password reset, Lecture_Examples folder, and WebSocket cleanup"
git push origin staging

# Create PR on GitHub:
# staging → main
# Title: "Production Deploy: Password Reset + Lecture_Examples Folder"
```

#### Step 1.3: Merge to Main (Triggers Auto-Deploy)
```bash
# On GitHub, merge the PR
# GitHub Actions will automatically:
# 1. Build Docker image
# 2. Push to ECR
# 3. Update ECS service
# 4. Deploy to production
```

**Monitor Deployment**:
```bash
# Watch GitHub Actions
# https://github.com/your-repo/actions

# Or monitor AWS ECS
aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-service \
  --region us-east-2
```

**Wait for**: `runningCount = 1` and `desiredCount = 1`

---

### **Phase 2: Run Migration (REQUIRED - 5 minutes)**

⚠️ **CRITICAL**: The `Lecture_Examples` folder will NOT be created automatically for existing students. You MUST run the migration script.

#### Step 2.1: Get Running Task ARN
```bash
aws ecs list-tasks \
  --cluster pythonide-cluster \
  --service-name pythonide-service \
  --region us-east-2
```

**Expected Output**:
```json
{
    "taskArns": [
        "arn:aws:ecs:us-east-2:653306034507:task/pythonide-cluster/abc123def456..."
    ]
}
```

#### Step 2.2: Run Migration Script
```bash
# Option A: AWS ECS Execute Command (Recommended)
aws ecs execute-command \
  --cluster pythonide-cluster \
  --task <TASK_ARN_FROM_ABOVE> \
  --container pythonide-backend \
  --command "python /app/server/migrations/add_examples_folder.py" \
  --interactive \
  --region us-east-2
```

**Expected Output**:
```
=== ADDING EXAMPLES FOLDERS TO STUDENT DIRECTORIES ===
Base path: /mnt/efs/pythonide-data/ide/Local
CREATED: sa8820/Lecture_Examples
CREATED: na3649/Lecture_Examples
CREATED: ntb5594/Lecture_Examples
...
CREATED: test_10/Lecture_Examples

=== MIGRATION SUMMARY ===
Total students: 60
✅ Created: 60
⏭️  Already exists: 0
❌ Errors: 0
✅ Migration complete!
```

#### Step 2.3: Verify Migration in Logs
```bash
aws logs tail /aws/ecs/pythonide --follow --region us-east-2 | grep "MIGRATION SUMMARY"
```

---

### **Phase 3: Testing (15 minutes)**

#### Test 1: Password Change (Student)
1. Login as `test_1` (password: `student@test_1`)
2. Click profile icon → "Change Password" tab
3. Enter:
   - Current password: `student@test_1`
   - New password: `TestPassword123`
   - Confirm: `TestPassword123`
4. Click "Change Password"
5. **Expected**: ✅ Success message
6. Logout and login with new password
7. **Expected**: ✅ Login succeeds

#### Test 2: Admin Access Control
1. Login as `test_1`
2. Navigate to: `https://pythonide-classroom.tech/admin/users`
3. **Expected**: ❌ Alert "Access Denied: Only admin_editor can access this page"
4. **Expected**: ❌ Redirected to `/editor`
5. Logout, login as `admin_editor`
6. Navigate to: `https://pythonide-classroom.tech/admin/users`
7. **Expected**: ✅ Admin Password Manager page loads

#### Test 3: Admin Password Reset
1. Login as `admin_editor`
2. Go to `/admin/users`
3. Find `test_2` in the user list
4. Click "Reset Password" button
5. Confirm the action
6. **Expected**: ✅ New random password displayed
7. Copy the new password
8. Logout, try logging in as `test_2` with **old** password
9. **Expected**: ❌ Login fails
10. Login as `test_2` with **new** password
11. **Expected**: ✅ Login succeeds

#### Test 4: Lecture_Examples Folder
1. Login as `test_1`
2. Open file browser in IDE
3. Navigate to `Local/test_1/`
4. **Expected**: ✅ See `Lecture_Examples` folder (alongside `workspace`, `submissions`)
5. Right-click `Lecture_Examples` → New File → `example1.py`
6. **Expected**: ✅ File created successfully
7. Write some code, save file
8. **Expected**: ✅ File saves successfully

#### Test 5: WebSocket Cleanup (File Switch)
1. Login as `test_1`
2. Open `Local/test_1/welcome.py`
3. Click "Run" button
4. **Expected**: ✅ Script runs, output appears
5. Immediately switch to another file (e.g., `workspace/test.py`)
6. Click "Run" on new file
7. **Expected**: ✅ Old script stops, new script runs
8. **Expected**: ❌ NO "file already running" error
9. Check browser console (F12)
10. **Expected**: ❌ NO "unknown error" messages

#### Test 6: WebSocket Cleanup (Browser Close)
1. Login as `test_1`
2. Open `Local/test_1/welcome.py`
3. Click "Run" button
4. While script is running, close browser tab
5. Check AWS CloudWatch Logs:
   ```bash
   aws logs tail /aws/ecs/pythonide --follow --region us-east-2 | grep "CLEANUP\|LOCK"
   ```
6. **Expected**: ✅ See cleanup messages:
   ```
   [SimpleExecutorV3-CLEANUP] Released execution lock
   [HANDLER-INFO-STOP] Stopped all subprograms
   WebSocket connection closed: user=test_1
   ```

---

### **Phase 4: Monitoring (2 hours)**

#### Monitor Logs for Errors
```bash
# Watch for errors
aws logs tail /aws/ecs/pythonide --follow --region us-east-2 | grep -i "error\|exception"

# Watch for WebSocket issues
aws logs tail /aws/ecs/pythonide --follow --region us-east-2 | grep "WebSocket\|CLEANUP\|LOCK"

# Watch for password changes
aws logs tail /aws/ecs/pythonide --follow --region us-east-2 | grep "password"
```

#### Check ECS Service Health
```bash
aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-service \
  --region us-east-2 \
  --query 'services[0].{runningCount:runningCount,desiredCount:desiredCount,status:status}'
```

**Expected**:
```json
{
    "runningCount": 1,
    "desiredCount": 1,
    "status": "ACTIVE"
}
```

#### Monitor User Activity
- Ask 2-3 students to test the IDE
- Watch for any error reports
- Monitor CloudWatch for unusual activity

---

## 🔄 Rollback Plan (If Issues Occur)

### Quick Rollback (< 5 minutes)
```bash
# Get previous task definition revision
aws ecs describe-task-definition \
  --task-definition pythonide-task \
  --region us-east-2 \
  --query 'taskDefinition.revision'

# Revert to previous revision (e.g., if current is 10, revert to 9)
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-service \
  --task-definition pythonide-task:9 \
  --region us-east-2

# Wait for rollback to complete
aws ecs wait services-stable \
  --cluster pythonide-cluster \
  --services pythonide-service \
  --region us-east-2
```

### Rollback Migration (If Needed)
```bash
# Delete Lecture_Examples folders (if causing issues)
aws ecs execute-command \
  --cluster pythonide-cluster \
  --task <TASK_ARN> \
  --container pythonide-backend \
  --command "find /mnt/efs/pythonide-data/ide/Local -type d -name 'Lecture_Examples' -exec rm -rf {} +" \
  --interactive \
  --region us-east-2
```

---

## 📊 Success Criteria

### Deployment Successful If:
- ✅ ECS service running (runningCount = 1)
- ✅ No errors in CloudWatch logs for 15 minutes
- ✅ Students can login
- ✅ Students can change password
- ✅ Admin can access `/admin/users`
- ✅ Admin can reset user passwords
- ✅ `Lecture_Examples` folder visible in all student directories
- ✅ No "file already running" errors
- ✅ No "unknown error" in browser console
- ✅ WebSocket connections properly close

### Known Issues (Expected):
- ⚠️ If migration script not run, `Lecture_Examples` folder won't appear (this is expected, just run migration)

---

## 📝 Post-Deployment Tasks

### 1. Announce to Students (Email Template)
```
Subject: IDE Update - New Features Available

Hi everyone,

We've updated the Python IDE with new features:

1. **Password Change**: You can now change your password from the Profile menu (top right icon).

2. **Lecture Examples Folder**: A new "Lecture_Examples" folder has been added to your workspace for class materials.

Please let me know if you encounter any issues.

Best,
[Your Name]
```

### 2. Update Documentation
- [x] TESTING_GUIDE.md created
- [x] WEBSOCKET_LIFECYCLE_AUDIT.md created
- [x] DEPLOYMENT_CHECKLIST.md created
- [ ] Update CLAUDE.md with new features

### 3. Monitor for 24 Hours
- [ ] Check logs daily for first 3 days
- [ ] Ask students for feedback
- [ ] Monitor CloudWatch metrics

---

## ⚠️ Important Notes

### Why Migration Script Doesn't Run Automatically

**Container Startup Flow**:
```
1. Docker container starts on ECS
2. auto_init_users.py runs automatically
3. Checks: Do users exist in PostgreSQL database?
   ├─ YES (60+ students exist) → SKIP directory creation
   └─ NO (fresh install) → Create users + directories
```

**Your Case**:
- All 60+ students already exist in the database
- `auto_init_users.py` will **skip** directory creation
- The migration script **must be run manually** after deployment

### Files Modified vs New Folders Created

| File Modified | Effect on Existing Users | Effect on New Users |
|---------------|--------------------------|---------------------|
| `file_storage.py` | ❌ No effect | ✅ Auto-creates folder |
| `auto_init_users.py` | ❌ No effect | ✅ Auto-creates folder |
| `add_examples_folder.py` | ✅ Run manually | ❌ Not needed |

---

## 🎯 Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Code Deployment | 5-10 min | Pending |
| Migration Script | 5 min | Pending |
| Testing | 15 min | Pending |
| Monitoring | 2 hours | Pending |
| **Total** | **~2.5 hours** | **Ready** |

---

## 📞 Emergency Contacts

- **Project Lead**: Sachin Adlakha (sa9082@nyu.edu)
- **AWS Console**: https://console.aws.amazon.com/
- **GitHub Repo**: [Your Repo URL]
- **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch/

---

## ✅ Final Checklist Before Deploy

- [ ] Frontend built (`npm run build`)
- [ ] All tests pass locally
- [ ] WebSocket cleanup verified (see WEBSOCKET_LIFECYCLE_AUDIT.md)
- [ ] Migration script tested locally
- [ ] Rollback plan understood
- [ ] Monitoring commands ready
- [ ] Emergency contacts available
- [ ] Pull request created (staging → main)

**Once all checked, proceed with deployment!**

---

_Last Updated: 2025-11-04_
_Version: 1.0_
_Deployed By: [Your Name]_
