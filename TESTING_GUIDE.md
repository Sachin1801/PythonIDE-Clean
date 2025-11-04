# Testing Guide: Password Reset & Examples Folder

## Changes Implemented

### 1. ✅ Student Password Change Re-enabled
- **File**: `src/components/element/UserProfileModal.vue`
- **What**: Students can now change their own password through the Profile modal
- **How**:
  - Click on profile icon → "Change Password" tab
  - Enter current password, new password (min 6 chars), confirm new password
  - Backend validates old password before updating

### 2. ✅ Admin Password Manager - Authentication Added
- **File**: `src/router/index.js`
- **What**: Only `admin_editor` account can access `/admin/users` route
- **How**:
  - Route guard checks if user is logged in
  - Verifies username is exactly `admin_editor`
  - Redirects non-admin users to `/editor` with alert
  - Admin can still reset passwords for all users and export to CSV

### 3. ✅ Examples Folder Added
- **Files**:
  - `server/common/file_storage.py` (line 78)
  - `server/auto_init_users.py` (line 309-310)
- **What**: All students now get an "Examples" folder in their Local directory
- **Structure**:
  ```
  Local/
  ├── {username}/
  │   ├── workspace/         # Student work area
  │   ├── Examples/          # NEW - Example files folder
  │   ├── submissions/       # Submitted assignments
  │   └── welcome.py         # Welcome file
  ```

### 4. ✅ Migration Script Created
- **File**: `server/migrations/add_examples_folder.py`
- **What**: Adds "Examples" folder to all existing student directories
- **Usage**: Run once after deployment to update existing students

---

## Testing Plan

### Phase 1: Local Testing

#### A. Test Password Change (Student)
1. **Start local services**:
   ```bash
   # Terminal 1: Start backend
   cd server
   python server.py --port 10086

   # Terminal 2: Start frontend
   npm run serve
   ```

2. **Test student password change**:
   - Login as a test student (e.g., `test_1` / `student@test_1`)
   - Click profile icon (top right)
   - Go to "Change Password" tab
   - Enter current password: `student@test_1`
   - Enter new password: `NewPassword123`
   - Confirm password: `NewPassword123`
   - Click "Change Password"
   - **Expected**: Success message, password updated
   - Logout and try logging in with new password
   - **Expected**: Login succeeds with new password

3. **Test wrong old password**:
   - Try changing password with wrong current password
   - **Expected**: Error "Invalid old password"

#### B. Test Admin Password Manager
1. **Test non-admin access block**:
   - Login as student (e.g., `test_1`)
   - Navigate to `http://localhost:8080/admin/users`
   - **Expected**: Alert "Access Denied: Only admin_editor can access this page"
   - **Expected**: Redirected to `/editor`

2. **Test admin access**:
   - Login as `admin_editor` (get password from admin)
   - Navigate to `http://localhost:8080/admin/users`
   - **Expected**: Admin Password Manager page loads
   - **Expected**: Can see list of all users

3. **Test password reset**:
   - Click "Reset Password" button for `test_1`
   - Confirm the action
   - **Expected**: New random password generated and displayed
   - Copy the new password
   - Logout, try logging in as `test_1` with old password
   - **Expected**: Login fails
   - Login as `test_1` with new password
   - **Expected**: Login succeeds

#### C. Test Examples Folder Creation
1. **Run migration script** (for existing users):
   ```bash
   cd server
   python migrations/add_examples_folder.py
   ```
   - **Expected**: Script creates "Examples" folder for all students
   - **Expected**: Summary shows count of created/existing folders

2. **Verify folder structure**:
   ```bash
   ls -la /tmp/pythonide-data/ide/Local/test_1/
   ```
   - **Expected**: See `workspace/`, `Examples/`, `submissions/`, `welcome.py`

3. **Test in IDE**:
   - Login as `test_1`
   - Open file browser in IDE
   - **Expected**: See "Examples" folder in `Local/test_1/`
   - Try creating a file in Examples folder
   - **Expected**: File creation succeeds (read-write access)

---

### Phase 2: Staging Testing

#### Prerequisites
- Code pushed to a staging branch (e.g., `feat/password-examples`)
- GitHub Actions deployed to staging environment

#### A. Deploy to Staging
```bash
# Build Docker image for staging
docker build --platform linux/amd64 -f Dockerfile -t pythonide-backend:staging .

# Push to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 653306034507.dkr.ecr.us-east-2.amazonaws.com
docker tag pythonide-backend:staging 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:staging
docker push 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:staging

# Update staging service
aws ecs update-service --cluster pythonide-staging-cluster --service pythonide-staging-service --force-new-deployment --region us-east-2
```

#### B. Run Migration on Staging EFS
```bash
# SSH into staging container or run as ECS task
docker exec -it <container-id> python /app/server/migrations/add_examples_folder.py
```

#### C. Test on Staging URL
Follow the same tests as Local Testing but on staging URL:
- Student password change
- Admin authentication
- Examples folder visibility in IDE

#### D. Verify Logs
```bash
aws logs tail /aws/ecs/pythonide-staging --follow --region us-east-2
```
- Check for errors during password changes
- Verify admin route authentication logs
- Check file operations in Examples folder

---

### Phase 3: Production Deployment

#### Prerequisites
- All staging tests passed
- Code merged to `main` branch
- Backup taken (database snapshot + EFS backup)

#### A. Pre-deployment Checklist
- [ ] All staging tests passed
- [ ] Database backup completed
- [ ] EFS snapshot created
- [ ] Rollback plan documented
- [ ] Communication sent to users (if downtime expected)

#### B. Deploy to Production
```bash
# GitHub Actions will auto-deploy when pushing to main
git checkout main
git merge feat/password-examples
git push origin main
```

Or manually:
```bash
# Build and push production image
docker build --platform linux/amd64 -f Dockerfile -t pythonide-backend:latest .
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 653306034507.dkr.ecr.us-east-2.amazonaws.com
docker tag pythonide-backend:latest 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:latest
docker push 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:latest

# Update production service
aws ecs update-service --cluster pythonide-cluster --service pythonide-service --force-new-deployment --region us-east-2
```

#### C. Run Migration on Production EFS
```bash
# SSH into production container or run as ECS task
docker exec -it <container-id> python /app/server/migrations/add_examples_folder.py
```

#### D. Post-deployment Verification
1. **Smoke Tests** (within 5 minutes):
   - Can admin login?
   - Can students login?
   - Can students change password?
   - Can admin access `/admin/users`?
   - Are Examples folders visible?

2. **Monitor Logs** (15 minutes):
   ```bash
   aws logs tail /aws/ecs/pythonide --follow --region us-east-2
   ```

3. **User Testing** (1 hour):
   - Ask 2-3 students to test password change
   - Verify Examples folder appears in their IDE
   - Check for any error reports

---

## Rollback Plan

If issues occur in production:

### Quick Rollback (< 5 minutes)
```bash
# Revert to previous Docker image
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-service \
  --task-definition pythonide-task:PREVIOUS_REVISION \
  --region us-east-2
```

### Database Rollback (if needed)
```bash
# Restore from RDS snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier pythonide-db-restore \
  --db-snapshot-identifier <snapshot-id> \
  --region us-east-2
```

### File System Rollback
- EFS data is persistent, Examples folders are harmless
- No rollback needed unless critical file corruption

---

## Expected Results

### Success Criteria
- ✅ Students can change their own passwords
- ✅ Only `admin_editor` can access admin password manager
- ✅ Admin can reset any user's password to random alphanumeric
- ✅ All students have "Examples" folder in their Local directory
- ✅ Examples folder has read-write permissions
- ✅ No errors in logs during password operations
- ✅ No performance degradation

### Known Limitations
- Forgot password flow still requires admin contact (by design)
- Admin password reset immediately invalidates user sessions (expected)
- Examples folder will be empty initially (expected)

---

## Support & Troubleshooting

### Common Issues

**Issue**: Student can't change password (wrong old password)
- **Solution**: Ask them to try forgot password flow, contact admin

**Issue**: Admin page shows blank/loading
- **Solution**: Clear localStorage, re-login as admin_editor

**Issue**: Examples folder not appearing
- **Solution**: Run migration script again, check file permissions

**Issue**: Password reset not working
- **Solution**: Check `/api/change-password` endpoint logs, verify bcrypt is working

---

## Contact

- **Project Lead**: Sachin Adlakha (sa9082@nyu.edu)
- **Production URL**: https://pythonide-classroom.tech/editor
- **Admin URL**: https://pythonide-classroom.tech/admin/users
- **AWS Region**: us-east-2

---

## Deployment Timeline

| Phase | Duration | Activity |
|-------|----------|----------|
| Local Testing | 1 hour | Test all features locally |
| Staging Deploy | 30 min | Deploy to staging + run migration |
| Staging Testing | 1 hour | Full test suite on staging |
| Production Deploy | 30 min | Deploy to production + migration |
| Monitoring | 2 hours | Watch logs, user feedback |
| **Total** | **5 hours** | **Complete deployment cycle** |

---

_Last Updated: 2025-11-03_
_Version: 1.0_
