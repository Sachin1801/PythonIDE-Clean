# AWS Production Deployment - Manual Steps Required

## ✅ Deployment Status
- **Task ID**: `30ecd408b9cb4c38b98c4792c7283282`
- **Status**: RUNNING ✅
- **Container**: pythonide-backend

## 🔧 STEP 1: Connect to AWS Container

Open a terminal and run:

```bash
aws ecs execute-command \
  --cluster pythonide-cluster \
  --task 30ecd408b9cb4c38b98c4792c7283282 \
  --container pythonide-backend \
  --command "/bin/bash" \
  --interactive \
  --region us-east-2
```

## 📝 STEP 2: Run Production Migration

Once connected to the container, execute:

```bash
cd /app/server
python3 migrations/create_full_class_with_consistent_passwords.py --environment production
```

### Expected Output:
```
============================================================
REMOVING ALL EXISTING USERS
============================================================
...
============================================================
CREATING 42 USERS WITH CONSISTENT PASSWORDS (PRODUCTION)
============================================================
...
✓ Credentials exported to: /app/adminData/consistent_class_credentials_production_YYYYMMDD_HHMMSS.csv
```

## 🔑 STEP 3: Save Admin Passwords

**Production Admin Passwords:**
- **admin_editor**: `XuR0ibQqhw6#`
- **sa9082**: `pXzwjLIYE20*`
- **sl7927**: `4qPg1cmJkUa!`
- **et2434**: `evaTQRwfyhC*`
- **test_admin**: `vheiJy81N8F#`

## 🌐 STEP 4: Test Admin Interface

1. Navigate to: https://pythonide-alb-456687384.us-east-2.elb.amazonaws.com/admin/users
2. Login with: `admin_editor` / `XuR0ibQqhw6#`
3. Verify:
   - ✅ Can see all 42 users
   - ✅ Pagination works (20 per page)
   - ✅ Password reset shows new password
   - ✅ Modal has white background (not transparent)

## 📥 STEP 5: Download Student Credentials

### Option A: Direct from Container
```bash
aws ecs execute-command \
  --cluster pythonide-cluster \
  --task 30ecd408b9cb4c38b98c4792c7283282 \
  --container pythonide-backend \
  --command "cat /app/adminData/consistent_class_credentials_production_*.csv" \
  --region us-east-2 > production_credentials.csv
```

### Option B: From Within Container
```bash
# Inside container
cat /app/adminData/consistent_class_credentials_production_*.csv
# Copy output to local file
```

## ✅ STEP 6: Verify Everything Works

### Test Student Login:
1. Pick a student from CSV (e.g., `jd1234`)
2. Navigate to: https://pythonide-alb-456687384.us-east-2.elb.amazonaws.com
3. Login with student credentials
4. Verify:
   - ✅ Can access `Local/jd1234/` directory
   - ✅ Can create/edit/run Python files
   - ✅ Cannot access other students' directories

### Test Admin Features:
1. Login as `admin_editor` at `/admin/users`
2. Reset a student's password
3. Verify new password is displayed
4. Try bulk password reset
5. Download new CSV

## 📊 STEP 7: Monitor Health

```bash
# Check task status
aws ecs describe-tasks \
  --cluster pythonide-cluster \
  --tasks 30ecd408b9cb4c38b98c4792c7283282 \
  --region us-east-2 \
  --query 'tasks[0].lastStatus' \
  --output text

# Check recent logs
aws logs get-log-events \
  --log-group-name /ecs/pythonide-backend \
  --log-stream-name ecs/pythonide-backend/d72d91c5480d4f8ab854443567084403 \
  --region us-east-2 \
  --limit 50 \
  --query 'events[*].message' \
  --output text
```

## 🎯 Success Criteria

- [ ] All 42 users created in production
- [ ] Admin can login at `/admin/users`
- [ ] Students can login with their credentials
- [ ] File isolation works (students only see their directories)
- [ ] Password reset functionality works
- [ ] CSV export contains all user credentials

## 📋 Next Steps

1. Share production URL with students
2. Distribute credentials securely
3. Monitor first day usage
4. Be ready to reset passwords if needed

---

**Production URL**: https://pythonide-alb-456687384.us-east-2.elb.amazonaws.com
**Admin Panel**: https://pythonide-alb-456687384.us-east-2.elb.amazonaws.com/admin/users