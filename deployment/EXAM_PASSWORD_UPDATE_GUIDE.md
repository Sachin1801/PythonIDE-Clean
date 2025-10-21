# 🔐 Exam Password Update & Production Deployment Guide

## Overview
This guide covers updating exam account passwords to lowercase alphanumeric format and deploying to production.

---

## ✅ What Changed

### Password Format:
- **Old Format**: 5-character uppercase letters + digits (e.g., `UTQ9T`, `YAWQF`)
- **New Format**: 5-character lowercase letters + digits (e.g., `6j5mj`, `32ap4`)

### Files Modified:
- `server/init_exam_users.py` (lines 16-20, 125-128)

---

## 📋 Step-by-Step Production Deployment

### Step 1: Test Locally (Docker Environment)

1. **Start local exam database**:
   ```bash
   cd /home/sachinadlakha/on-campus/PythonIDE-Clean
   docker-compose -f docker-compose.exam.yml up -d pythonide-exam-db
   ```

2. **Wait for database to be ready** (about 10 seconds):
   ```bash
   sleep 10
   ```

3. **Set environment variable for exam database**:
   ```bash
   export EXAM_DATABASE_URL="postgresql://exam_admin:ExamSecurePass2024@localhost:5433/pythonide_exam"
   ```

4. **Run the updated script to regenerate passwords**:
   ```bash
   cd server
   uv run python init_exam_users.py --reset
   ```

5. **Verify the CSV was created**:
   ```bash
   ls -lh ../adminData/exam_credentials_*.csv
   ```

6. **Preview the new credentials** (first 10 lines):
   ```bash
   head -10 ../adminData/exam_credentials_*.csv
   ```

7. **Test login with new credentials**:
   ```bash
   # Start the exam IDE locally
   docker-compose -f docker-compose.exam.yml up -d

   # Check logs
   docker-compose -f docker-compose.exam.yml logs pythonide
   ```

8. **Manual login test**:
   - Open browser: http://localhost:8080
   - Login with: `exam_sa8820` / `[password from CSV]`
   - Verify you can access the exam environment

9. **Stop local testing**:
   ```bash
   docker-compose -f docker-compose.exam.yml down
   ```

---

### Step 2: Deploy to AWS Production

#### Option A: Update Production Exam Database (RECOMMENDED)

1. **Set production exam database URL**:
   ```bash
   export EXAM_DATABASE_URL="postgresql://exam_admin:ExamSecurePass2024@pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432/pythonide_exam"
   ```

2. **Run script to update production**:
   ```bash
   cd /home/sachinadlakha/on-campus/PythonIDE-Clean/server
   uv run python init_exam_users.py --reset
   ```

3. **Verify credentials saved**:
   ```bash
   # Find the latest CSV
   ls -lt ../adminData/exam_credentials_*.csv | head -1

   # Preview credentials
   cat ../adminData/exam_credentials_[timestamp].csv
   ```

4. **Test production login**:
   - Open: http://exam.pythonide-classroom.tech/
   - Login with: `exam_sa8820` / `[new password from CSV]`
   - Verify access works

---

### Step 3: Distribute New Credentials

1. **Copy the latest CSV**:
   ```bash
   # Find the latest CSV file
   cd /home/sachinadlakha/on-campus/PythonIDE-Clean/adminData
   latest_csv=$(ls -t exam_credentials_*.csv | head -1)

   # Copy to a safe location
   cp "$latest_csv" exam_credentials_LATEST.csv
   ```

2. **Create individual credential slips** (optional):
   ```bash
   # Create a Python script to generate printable slips
   cat > create_credential_slips.py << 'EOF'
import csv

with open('exam_credentials_LATEST.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Username'].startswith('exam_'):
            print(f"""
============================================
   MID-TERM EXAM LOGIN CREDENTIALS
============================================
Student: {row['Full Name']}
Username: {row['Username']}
Password: {row['Password']}
URL: http://exam.pythonide-classroom.tech/
============================================
            """)
EOF

   python create_credential_slips.py > credential_slips.txt
   ```

3. **Distribute to students**:
   - Email individually (recommended)
   - Print slips and hand out in person
   - Post in secure LMS (Canvas/Blackboard)

---

### Step 4: Production Testing Checklist

#### Test Case 1: Student Login
- [ ] Go to http://exam.pythonide-classroom.tech/
- [ ] Login as `exam_sa8820` with new password
- [ ] Verify you see only `exam_sa8820` folder in file tree
- [ ] Create a test file and run Python code
- [ ] Logout

#### Test Case 2: Professor Login
- [ ] Login as `exam_sa9082` / `ExamAdmin@sa9082`
- [ ] Verify you can see all exam student folders
- [ ] Access a student's folder (e.g., `exam_sa8820`)
- [ ] Verify read access works

#### Test Case 3: Isolation Verification
- [ ] Login as student `exam_sa8820`
- [ ] Verify you CANNOT see other students' folders
- [ ] Verify you CANNOT navigate to `/mnt/efs/pythonide-data-exam/ide/Local/exam_na3649`
- [ ] Logout

#### Test Case 4: Password Security
- [ ] All passwords are 5 characters
- [ ] All passwords use lowercase letters (a-z) and digits (2-9)
- [ ] No ambiguous characters (0, o, 1, l)
- [ ] Each password is unique

---

### Step 5: Backup & Security

1. **Backup the CSV**:
   ```bash
   cd /home/sachinadlakha/on-campus/PythonIDE-Clean/adminData

   # Create encrypted backup
   gpg -c exam_credentials_LATEST.csv

   # Store in secure location
   mv exam_credentials_LATEST.csv.gpg ~/secure_backup/
   ```

2. **Share credentials securely**:
   - ✅ DO: Email individually with BCC
   - ✅ DO: Use password-protected PDF
   - ✅ DO: Hand out printed slips in person
   - ❌ DON'T: Post publicly
   - ❌ DON'T: Share via Slack/Discord
   - ❌ DON'T: Commit to Git

3. **Set file permissions**:
   ```bash
   chmod 600 adminData/exam_credentials_*.csv
   ```

---

## 🚨 Troubleshooting

### Issue: "EXAM_DATABASE_URL not set"
**Solution**:
```bash
export EXAM_DATABASE_URL="postgresql://exam_admin:ExamSecurePass2024@pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432/pythonide_exam"
```

### Issue: "Connection refused" when connecting to RDS
**Solution**:
1. Check security group allows your IP
2. Verify RDS endpoint is correct
3. Test connection:
   ```bash
   psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com -U exam_admin -d pythonide_exam
   ```

### Issue: Students can't login with new passwords
**Solution**:
1. Verify database was updated:
   ```bash
   psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com -U exam_admin -d pythonide_exam -c "SELECT username, substring(password_hash, 1, 10) FROM users WHERE username LIKE 'exam_%' LIMIT 5;"
   ```
2. Check CSV matches database
3. Verify ECS task is using latest Docker image

### Issue: CSV not created in adminData folder
**Solution**:
```bash
# Create directory manually
mkdir -p /home/sachinadlakha/on-campus/PythonIDE-Clean/adminData

# Re-run script
cd /home/sachinadlakha/on-campus/PythonIDE-Clean/server
uv run python init_exam_users.py --reset
```

---

## 📊 Verification Commands

### Check all exam users in database:
```bash
psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com -U exam_admin -d pythonide_exam -c "SELECT username, full_name, role FROM users WHERE username LIKE 'exam_%' ORDER BY username;"
```

### Count exam students:
```bash
psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com -U exam_admin -d pythonide_exam -c "SELECT COUNT(*) as student_count FROM users WHERE username LIKE 'exam_%' AND role='student';"
```

### Verify password hashes changed:
```bash
# Before running script, save old hashes
psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com -U exam_admin -d pythonide_exam -c "SELECT username, password_hash FROM users WHERE username='exam_sa8820';" > old_hash.txt

# After running script, compare
psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com -U exam_admin -d pythonide_exam -c "SELECT username, password_hash FROM users WHERE username='exam_sa8820';" > new_hash.txt

diff old_hash.txt new_hash.txt
```

---

## 📋 Complete Commands Summary

```bash
# 1. Export database URL
export EXAM_DATABASE_URL="postgresql://exam_admin:ExamSecurePass2024@pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432/pythonide_exam"

# 2. Navigate to server directory
cd /home/sachinadlakha/on-campus/PythonIDE-Clean/server

# 3. Run script to regenerate passwords (resets existing users)
uv run python init_exam_users.py --reset

# 4. Verify CSV created
ls -lh ../adminData/exam_credentials_*.csv

# 5. Preview credentials
cat ../adminData/exam_credentials_*.csv | head -10

# 6. Test production login
# Open browser: http://exam.pythonide-classroom.tech/
# Login: exam_sa8820 / [password from CSV]

# 7. Backup CSV
cp ../adminData/exam_credentials_*.csv ../adminData/exam_credentials_LATEST.csv
chmod 600 ../adminData/exam_credentials_*.csv
```

---

## ✅ Post-Deployment Checklist

- [ ] Script ran successfully without errors
- [ ] CSV file created in `adminData/` directory
- [ ] 41 student accounts + 3 professor accounts created/updated
- [ ] Tested login with at least 3 different student accounts
- [ ] Tested professor account can see all student folders
- [ ] CSV backed up securely
- [ ] Credentials distributed to students
- [ ] File permissions set to 600 on CSV files
- [ ] Old CSV files archived or deleted

---

## 🎯 Quick Reference

### Student Account Format:
- **Username**: `exam_{netid}` (e.g., `exam_sa8820`)
- **Password**: 5-char lowercase alphanumeric (e.g., `6j5mj`)
- **Count**: 41 students

### Professor Accounts:
- `exam_sl7927` / `ExamAdmin@sl7927` (Susan Liao)
- `exam_sa9082` / `ExamAdmin@sa9082` (Sachin Adlakha)
- `exam_et2434` / `ExamAdmin@et2434` (Ethan Tan)

### URLs:
- **Exam IDE**: http://exam.pythonide-classroom.tech/
- **Main IDE**: https://pythonide-classroom.tech/

---

*Last Updated: October 18, 2025*
