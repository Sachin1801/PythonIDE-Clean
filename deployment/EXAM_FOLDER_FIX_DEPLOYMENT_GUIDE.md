# 🔧 Exam Folder Naming Fix - Deployment Guide

## ✅ Changes Completed

All code changes have been implemented and are ready for deployment!

---

## 📋 Summary of Changes

### 1. **server/server.py** ✅
- **Line 257-266**: Added `IS_EXAM_MODE` check to skip `auto_init_users.py` in exam environment
- **Impact**: Main IDE unaffected, exam uses only `init_exam_users.py`

### 2. **server/init_exam_users.py** ✅
- **Line 208-216**: Changed env var from `EXAM_IDE_DATA_PATH` to `IDE_DATA_PATH` (matches docker-compose.exam.yml)
- **Line 275-286**: Updated welcome.py content to simple exam environment greeting
- **Impact**: Correct folders (`exam_sa8820`) created with proper welcome message

### 3. **server/common/file_storage.py** ✅
- **Line 57-67**: Added `validate_user_folder_name()` method with exam mode check
- **Line 71-72**: Added validation call in `create_user_directories()`
- **Impact**: Prevents creating folders with wrong names in exam environment

### 4. **server/cleanup_wrong_exam_folders.py** ✅ NEW FILE
- Complete cleanup script with safety checks
- Only targets exam environment paths
- Multiple safety checks to prevent main IDE deletion
- Supports dry-run and live modes

---

## 🚀 Deployment Steps

### Step 1: Test Cleanup Script (Dry Run)

First, let's see what would be deleted **without actually deleting**:

```bash
cd /home/sachinadlakha/on-campus/PythonIDE-Clean/server
uv run python cleanup_wrong_exam_folders.py --dry-run
```

**Expected Output:**
```
========================================================================
EXAM ENVIRONMENT FOLDER CLEANUP SCRIPT
========================================================================
Mode: DRY RUN (no actual deletion)

📂 Checking exam path: /mnt/efs/pythonide-data-exam/ide/Local
   Found X items in directory
   🔍 [DRY RUN] Would delete: sa8820
   🔍 [DRY RUN] Would delete: na3649
   ✅ Keeping correct folder: exam_sa8820
   ✅ Keeping correct folder: exam_na3649
   ...

========================================================================
CLEANUP SUMMARY
========================================================================
Total items checked: X
Folders that would be deleted: Y
⚠️  This was a DRY RUN - no actual deletion occurred
```

---

### Step 2: Run Cleanup Script (Live)

After confirming the dry run output looks correct, run the actual cleanup:

```bash
cd /home/sachinadlakha/on-campus/PythonIDE-Clean/server
uv run python cleanup_wrong_exam_folders.py --live
```

**You will be prompted:**
```
⚠️  WARNING: You are about to delete folders!
⚠️  This will only affect exam environment paths.
⚠️  Main IDE folders will NOT be touched.

Are you sure you want to continue? (yes/no):
```

Type `yes` to proceed.

**Expected Output:**
```
📂 Checking exam path: /mnt/efs/pythonide-data-exam/ide/Local
   🗑️  Deleting wrong folder: sa8820
   ✅ Deleted successfully: sa8820
   🗑️  Deleting wrong folder: na3649
   ✅ Deleted successfully: na3649
   ✅ Keeping correct folder: exam_sa8820
   ✅ Keeping correct folder: exam_na3649
   ...

========================================================================
CLEANUP SUMMARY
========================================================================
Folders deleted: 41
✅ Cleanup completed successfully!
```

---

### Step 3: Verify Cleanup

Check that only correct folders remain:

```bash
# For production (EFS)
ls -la /mnt/efs/pythonide-data-exam/ide/Local/

# Should see ONLY folders like:
# exam_sa8820/
# exam_na3649/
# exam_jh9963/
# (NO folders like sa8820, na3649, etc.)
```

---

### Step 4: Commit Changes to Git

```bash
cd /home/sachinadlakha/on-campus/PythonIDE-Clean

# Stage all changes
git add server/server.py
git add server/init_exam_users.py
git add server/common/file_storage.py
git add server/cleanup_wrong_exam_folders.py
git add deployment/EXAM_FOLDER_FIX_DEPLOYMENT_GUIDE.md

# Commit
git commit -m "fix: Correct exam folder naming to use exam_ prefix

- Skip auto_init_users.py when IS_EXAM_MODE=true
- Fix init_exam_users.py to use IDE_DATA_PATH env var
- Add folder naming validation for exam environment
- Create cleanup script for wrong folders
- Update welcome.py message for exam environment"

# Push to staging branch
git push origin staging
```

---

### Step 5: Deploy to Production (AWS ECS)

Since we're on the `staging` branch, we need to merge to `main` for auto-deployment:

```bash
# Switch to main branch
git checkout main

# Merge staging
git merge staging

# Push to main (triggers GitHub Actions deployment)
git push origin main
```

**GitHub Actions will automatically:**
1. Build new Docker image with platform linux/amd64
2. Push to ECR
3. Update ECS task definition
4. Deploy to production

**Monitor deployment:**
```bash
# Watch ECS service update
aws ecs describe-services --cluster pythonide-cluster --services pythonide-exam-task-service --region us-east-2

# Check logs
aws logs tail /aws/ecs/pythonide-exam --follow --region us-east-2
```

---

### Step 6: Verify Production Deployment

#### Test 1: Check Server Logs
```bash
# Should see this log message in exam environment:
# "Exam mode detected - skipping auto_init_users (exam uses init_exam_users.py)"

aws logs tail /aws/ecs/pythonide-exam --follow --region us-east-2 | grep "Exam mode"
```

#### Test 2: Verify Folders on EFS
```bash
# Connect to ECS task or EC2 instance with EFS mounted
# Check folder structure
ls -la /mnt/efs/pythonide-data-exam/ide/Local/

# Should see ONLY:
# exam_sa8820/
# exam_na3649/
# exam_jh9963/
# ... (all with exam_ prefix)
```

#### Test 3: Login and Verify
1. Open: http://exam.pythonide-classroom.tech/
2. Login with: `exam_sa8820` / `ggjm4`
3. Verify:
   - ✅ Can login successfully
   - ✅ See only `exam_sa8820` folder in file tree
   - ✅ Folder contains `welcome.py` with exam message
   - ✅ Can create and run Python files

#### Test 4: Verify Main IDE Unaffected
1. Open: https://pythonide-classroom.tech/
2. Login with: `sa8820` / `[their password]`
3. Verify:
   - ✅ Can login successfully
   - ✅ See `sa8820` folder (WITHOUT exam_ prefix)
   - ✅ All existing files intact
   - ✅ No impact on main IDE

---

## 📊 Verification Checklist

### Exam Environment:
- [ ] Only folders with `exam_` prefix exist in `/mnt/efs/pythonide-data-exam/ide/Local/`
- [ ] No folders like `sa8820`, `na3649` (without prefix)
- [ ] Each folder contains only `welcome.py` with exam message
- [ ] Students can login with `exam_{netid}` username
- [ ] Students see only their own folder
- [ ] Professors can see all exam folders

### Main IDE (Unchanged):
- [ ] Folders like `sa8820`, `na3649` (without prefix) still exist in `/mnt/efs/pythonide-data/ide/Local/`
- [ ] Students can login with regular username
- [ ] All existing files and folders intact
- [ ] No impact on functionality

---

## 🔧 Troubleshooting

### Issue: Cleanup script doesn't find any folders
**Solution:**
- Check if paths are correct
- Verify you're running on the right environment
- Check EFS is mounted: `ls /mnt/efs/pythonide-data-exam/`

### Issue: "Permission denied" when running cleanup
**Solution:**
```bash
# Run with proper permissions
sudo uv run python cleanup_wrong_exam_folders.py --live
```

### Issue: Wrong folders reappear after cleanup
**Solution:**
- This means the code changes haven't been deployed yet
- Rebuild and restart exam Docker container
- Verify `IS_EXAM_MODE=true` is set in environment

### Issue: Students can't login after cleanup
**Solution:**
- Check that correct folders (`exam_sa8820`) exist
- Verify database has exam users with correct usernames
- Check credentials CSV matches usernames

---

## 🎯 Quick Commands Reference

```bash
# 1. Dry run cleanup
cd /home/sachinadlakha/on-campus/PythonIDE-Clean/server
uv run python cleanup_wrong_exam_folders.py --dry-run

# 2. Live cleanup
uv run python cleanup_wrong_exam_folders.py --live

# 3. Verify folders
ls -la /mnt/efs/pythonide-data-exam/ide/Local/

# 4. Commit and push
git add -A
git commit -m "fix: Exam folder naming corrections"
git push origin staging

# 5. Deploy to production
git checkout main
git merge staging
git push origin main

# 6. Monitor deployment
aws ecs describe-services --cluster pythonide-cluster --services pythonide-exam-task-service --region us-east-2
aws logs tail /aws/ecs/pythonide-exam --follow --region us-east-2
```

---

## ✅ Success Criteria

**You'll know the fix is working when:**

1. ✅ Cleanup script successfully deletes wrong folders
2. ✅ Only `exam_{netid}` folders exist in exam environment
3. ✅ Students can login to exam environment
4. ✅ No new wrong folders are created after server restart
5. ✅ Main IDE continues working normally
6. ✅ Server logs show "Exam mode detected - skipping auto_init_users"

---

*Last Updated: October 19, 2025*
