# Testing and Routes Guide - Folder Upload & Bulk Upload

## 🚀 Quick Start - Local Testing

### Step 1: Start Backend Server

```bash
cd /home/sachinadlakha/on-campus/PythonIDE-Clean

# Start the backend server on port 10086
python server/server.py --port 10086
```

**Expected Output:**
```
✓ File storage initialized at: /tmp/pythonide-data
✓ Storage type: Local
Starting server on port 10086...
```

### Step 2: Start Frontend (in separate terminal)

```bash
cd /home/sachinadlakha/on-campus/PythonIDE-Clean

# Start dev server
npm run dev
```

**Expected Output:**
```
VITE v5.x.x ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

---

## 📍 Application Routes

### Local Development

| Page | URL | Description |
|------|-----|-------------|
| **Login Page** | `http://localhost:5173/` | Main login page |
| **IDE (Student)** | `http://localhost:5173/ide` | IDE interface for students |
| **IDE (Admin)** | `http://localhost:5173/ide` | Same IDE, admin features unlocked |

**Admin Accounts** (for testing bulk upload):
- `sl7927` - Admin
- `sa9082` - Admin
- `et2434` - Admin
- `admin_editor` - Admin
- `test_admin` - Admin

**Test Student Account**:
- `test_student` - Student (cannot access bulk upload)

---

### AWS Production

| Page | URL | Description |
|------|-----|-------------|
| **Production IDE** | `http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com/` | Main production URL |
| **Login** | `http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com/` | Login page |
| **IDE** | `http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com/ide` | IDE interface |

**Note**: There is NO separate "/admin" route. Admin features are accessible from the regular IDE interface when logged in as an admin user.

---

## 🧪 Testing Scenarios

### Test 1: Single File Upload

**Steps:**
1. Login as admin: `sl7927` (or any admin account)
2. Navigate to any student folder (e.g., `Local/test_student/`)
3. Look at left sidebar file tree, find the **Upload icon** button (4th button from left)
4. Click **Upload** button → Opens Import Files Dialog
5. Keep mode on "Files"
6. Select a single `.py` file from your computer
7. Click "Import"

**Expected Result:**
✅ File appears in the selected folder
✅ Success message: "Successfully imported 1 file(s)"

---

### Test 2: Folder Upload (Single Student)

**Prepare Test Data:**
Create a folder on your computer:
```
TestFolder/
  ├── file1.py
  ├── file2.txt
  └── subfolder/
      └── nested.py
```

**Steps:**
1. Login as admin
2. Navigate to `Local/test_student/Examples/`
3. Click **Upload** button (left sidebar)
4. **Switch to "Folder" mode** (toggle button)
5. Click the upload area or drag-drop the `TestFolder` folder
6. Verify all files are listed (3 files: file1.py, file2.txt, nested.py)
7. Click "Import 3 file(s)"

**Expected Result:**
✅ Folder structure is preserved:
```
Local/test_student/Examples/
  └── subfolder/
      ├── file1.py
      ├── file2.txt
      └── nested.py
```
✅ Success message shown

---

### Test 3: Bulk Upload to All Students

**Steps:**
1. Login as admin (`sa9082`)
2. Look at left sidebar file tree
3. Find the **Users icon** button (5th button, next to Upload) - This is the Bulk Upload button
4. Click **Bulk Upload to Students** button → Opens Bulk Upload Dialog
5. Select "All Students" (should show count like "All Students (40)")
6. Set destination folder: `Examples`
7. Optional: Set sub-path: `Week1`
8. Switch to "Files" or "Folder" mode
9. Select test file (e.g., `lecture.py`)
10. Click "Upload to XX Student(s)"

**Expected Result:**
✅ File uploaded to all students:
```
Local/sa9082/Examples/Week1/lecture.py
Local/test_student/Examples/Week1/lecture.py
... (all 40+ students)
```
✅ Success message: "Successfully uploaded 1 file(s) to 40 students"

---

### Test 4: Bulk Upload to Specific Students

**Steps:**
1. Login as admin
2. Click **Bulk Upload** button (Users icon)
3. Select "Specific Students"
4. Search for "test" in search box
5. Check 2-3 students (e.g., test_student, test_1, test_2)
6. Set destination: `Examples/Assignments`
7. Upload a file
8. Click "Upload to 3 Student(s)"

**Expected Result:**
✅ File uploaded only to selected 3 students
✅ Other students' folders unchanged

---

### Test 5: Folder Structure Preservation (Bulk Upload)

**Prepare Test Data:**
```
Week2_Materials/
  ├── lecture.py
  ├── homework/
  │   ├── problem1.py
  │   └── data/
  │       └── test.csv
```

**Steps:**
1. Login as admin
2. Click **Bulk Upload** button
3. Select "All Students"
4. Destination: `Examples`
5. Sub-path: ` ` (leave empty)
6. **Switch to "Folder" mode**
7. Select `Week2_Materials` folder
8. Click "Upload to XX Student(s)"

**Expected Result:**
✅ Each student gets complete folder structure:
```
Local/{username}/Examples/
  ├── lecture.py
  └── homework/
      ├── problem1.py
      └── data/
          └── test.csv
```

---

## 🔍 Verification Methods

### Method 1: Check UI (File Tree)
- Refresh the project tree (click Refresh button)
- Navigate to student folders
- Verify files/folders appear

### Method 2: Check Filesystem (Local)

```bash
# Check local development files
ls -la /tmp/pythonide-data/ide/Local/test_student/Examples/

# Should show uploaded files
```

### Method 3: Check Filesystem (AWS Production)

```bash
# Connect to ECS task
aws ecs execute-command \
  --cluster pythonide-cluster \
  --task <TASK_ID> \
  --container pythonide-backend \
  --command "/bin/bash" \
  --interactive \
  --region us-east-2

# Inside container:
ls -la /mnt/efs/pythonide-data/ide/Local/test_student/Examples/
```

### Method 4: Check Database

```bash
# Connect to PostgreSQL
psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com \
     -U pythonide_admin \
     -d pythonide

# Query file metadata
SELECT * FROM files WHERE path LIKE '%Examples%';
```

---

## 🐛 Troubleshooting

### Issue 1: "Only admin users can upload files"

**Cause**: Not logged in as admin
**Solution**: Login with admin account (sl7927, sa9082, et2434)

---

### Issue 2: Bulk Upload button not visible

**Cause**: Not logged in as admin or UI not refreshed
**Solution**:
1. Verify you're logged in as admin
2. Check console for errors: `F12` → Console tab
3. Refresh page: `Ctrl+Shift+R`

---

### Issue 3: "Failed to load student list"

**Cause**: Backend not running or API endpoint issue
**Solution**:
1. Check backend is running on port 10086
2. Check browser console for API errors
3. Verify `/api/get-all-students` endpoint works:
   ```bash
   curl -H "session-id: YOUR_SESSION_ID" http://localhost:10086/api/get-all-students
   ```

---

### Issue 4: Files not appearing after upload

**Cause**: Project tree not refreshed
**Solution**:
1. Click **Refresh** button (circular arrow) in sidebar
2. Check console logs for errors
3. Verify backend logs show successful upload

---

### Issue 5: Folder structure not preserved

**Cause**: Using "Files" mode instead of "Folder" mode
**Solution**:
1. Switch to **"Folder" mode** before selecting folder
2. Verify `preserveStructure: true` in browser network tab

---

## 📊 Expected Console Logs

### Successful Upload (Browser Console):
```javascript
[DialogImportFile] Upload params: {
  projectName: "Local/test_student",
  cleanedParentPath: "/Examples",
  uploadMode: "folder",
  fileCount: 3
}

[DialogImportFile] Folder upload: {
  filename: "file1.py",
  relativePath: "TestFolder/file1.py"
}
```

### Successful Bulk Upload (Browser Console):
```javascript
[BulkUpload] Loaded 40 students
[BulkUpload] Uploading to 40 students...
```

### Backend Logs (Terminal):
```
INFO - Folder upload - Relative path: Week1/lecture.py, Final path: /Examples/Week1/lecture.py
INFO - File uploaded successfully: Local/sa9082/Examples/Week1/lecture.py by sa9082
INFO - Bulk upload: lecture.py → Local/test_student/Examples/Week1/lecture.py (admin: sa9082)
INFO - Bulk upload complete: 40/40 successful
```

---

## 📋 Pre-Deployment Checklist

Before deploying to AWS, verify locally:

- [ ] Backend starts without errors
- [ ] Frontend compiles successfully
- [ ] Login works with admin account
- [ ] Single file upload works
- [ ] Folder upload preserves structure
- [ ] Bulk upload dialog opens for admins
- [ ] Student list loads in bulk upload dialog
- [ ] Bulk upload to all students works
- [ ] Bulk upload to specific students works
- [ ] Folder structure preserved in bulk upload
- [ ] Files persist after page refresh
- [ ] Non-admin users cannot access bulk upload

---

## 🚀 AWS Deployment Instructions

### Build and Push Docker Image

```bash
cd /home/sachinadlakha/on-campus/PythonIDE-Clean

# Build with correct platform for ECS
docker build --platform linux/amd64 -t pythonide-backend:latest .

# Login to ECR
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin \
  653306034507.dkr.ecr.us-east-2.amazonaws.com

# Tag and push
docker tag pythonide-backend:latest \
  653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:latest

docker push 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:latest
```

### Update ECS Service

```bash
# Force new deployment
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-service \
  --force-new-deployment \
  --region us-east-2

# Monitor deployment
aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-service \
  --region us-east-2
```

### Verify Deployment

```bash
# Check logs
aws logs tail /aws/ecs/pythonide --follow --region us-east-2

# Look for:
# ✓ File storage initialized at: /mnt/efs/pythonide-data
# ✓ Storage type: AWS EFS
```

---

## 🔐 Security Notes

1. **Admin-only endpoints**: `/api/upload-file`, `/api/bulk-upload`, `/api/get-all-students` are restricted to admin accounts
2. **File type validation**: Only `.py`, `.txt`, `.csv`, `.pdf` allowed
3. **File size limit**: 10MB per file
4. **Path sanitization**: Prevents directory traversal attacks
5. **Session validation**: All requests require valid session ID

---

## 📞 Support

If you encounter issues:

1. **Check browser console**: `F12` → Console tab
2. **Check backend logs**: Terminal running `python server/server.py`
3. **Check network requests**: `F12` → Network tab
4. **Review [FOLDER_UPLOAD_IMPLEMENTATION.md](FOLDER_UPLOAD_IMPLEMENTATION.md)** for detailed documentation
5. **Review [CLAUDE.md](CLAUDE.md)** for project context

---

## ✅ Success Indicators

You'll know everything is working when:

✅ Admin can see **Users icon** (bulk upload) button in sidebar
✅ Import dialog has "Files" / "Folder" toggle
✅ Bulk upload dialog shows student count
✅ Files upload successfully and appear in file tree
✅ Folder structures are preserved after upload
✅ Bulk uploads reach all/selected students
✅ Non-admin users cannot access bulk upload features

---

**Last Updated**: January 2025
**Tested On**: Node.js v20+, Python 3.11+, AWS ECS Fargate
