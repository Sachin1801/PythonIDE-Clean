# Folder Upload & Bulk Upload Implementation

## Overview
Complete implementation of folder upload functionality with bulk upload capabilities for the PythonIDE-Clean project. This allows admins to upload files/folders to single or multiple students' directories while preserving folder structures.

## Implementation Summary

### ✅ Phase 1: Folder Upload to Single Destination
**Goal**: Enable uploading folders to a single student's directory while preserving structure.

**Changes Made**:

1. **Frontend: [DialogImportFile.vue](src/components/element/pages/ide/dialog/DialogImportFile.vue)**
   - Added upload mode toggle (Files/Folder)
   - Implemented `webkitdirectory` support for folder selection
   - Added folder structure traversal for drag-and-drop
   - Created `processFolderFiles()` method to handle relative paths
   - UI shows folder hierarchy preservation

2. **Backend: [upload_handler.py](server/handlers/upload_handler.py)**
   - Enhanced to accept `relativePath` and `preserveStructure` parameters
   - Automatically creates nested directory structures
   - Preserves folder hierarchy from client
   - Example: `Week1/homework/test.py` → `Local/sa9082/Examples/Week1/homework/test.py`

### ✅ Phase 2: Bulk Upload to Multiple Students
**Goal**: Allow admins to upload files/folders to ALL students' common folders simultaneously.

**Changes Made**:

1. **Backend: [bulk_upload_handler.py](server/handlers/bulk_upload_handler.py)** (NEW)
   - New `/api/bulk-upload` endpoint
   - Supports uploading to "all students" or specific students
   - Preserves folder structures for each student
   - Returns detailed success/failure statistics

2. **Database: [user_manager_postgres.py](server/auth/user_manager_postgres.py)**
   - Added `get_all_students()` method
   - Fetches all users with `role='student'` from database

3. **Server: [server.py](server/server.py)**
   - Registered `/api/bulk-upload` route
   - Imported `BulkUploadHandler`

4. **Frontend: [DialogBulkUpload.vue](src/components/element/pages/ide/dialog/DialogBulkUpload.vue)** (NEW)
   - Admin-only dialog for bulk uploads
   - Student selection: All students OR specific students
   - Common folder configuration (e.g., "Examples/Week1")
   - Folder/file upload support with preview

### ✅ Phase 3: Reusable Upload Logic
**Goal**: Create reusable composable for upload functionality across the application.

**Changes Made**:

1. **Composable: [useFileUpload.js](src/composables/useFileUpload.js)** (NEW)
   - Reusable Vue 3 composable
   - Methods:
     - `processFiles()` - Process individual files
     - `processFolderFiles()` - Process folders with structure
     - `uploadFiles()` - Upload to single destination
     - `bulkUploadFiles()` - Upload to multiple students
     - `traverseFileTree()` - Handle drag-and-drop folders
     - `formatFileSize()` - Utility for display
   - Can be used in any component (IDE, Admin Dashboard, etc.)

---

## File Structure & Permissions

### EFS Path Configuration (Production & Local)

**Path Resolution Logic** ([file_storage.py](server/common/file_storage.py:22-33)):
```python
def _get_storage_root(self):
    # 1. Check environment variable (Docker/ECS)
    if "IDE_DATA_PATH" in os.environ:
        return os.environ["IDE_DATA_PATH"]

    # 2. AWS EFS (Production)
    if os.path.exists("/mnt/efs/pythonide-data"):
        return "/mnt/efs/pythonide-data"

    # 3. Local development
    return "/tmp/pythonide-data"
```

**Directory Structure**:
```
/mnt/efs/pythonide-data/     (AWS Production)
OR
/tmp/pythonide-data/          (Local Development)
  └── ide/
      ├── Local/
      │   ├── sa9082/
      │   │   ├── Examples/
      │   │   │   ├── Week1/
      │   │   │   └── Week2/
      │   │   ├── workspace/
      │   │   └── submissions/
      │   ├── jd1234/
      │   │   └── Examples/
      │   └── ... (60+ students)
      └── Lecture Notes/
```

**Permissions**:
- **Students**: Read-write access to `Local/{username}/` only
- **Professors/Admins**: Full read-write access to all directories

---

## API Documentation

### 1. `/api/upload-file` (Enhanced)
**Purpose**: Upload single/multiple files to a specific destination

**Request**:
```javascript
FormData:
  - file: File
  - projectName: "Local/sa9082"
  - parentPath: "/Examples"
  - filename: "test.py"
  - relativePath: "Week1/homework/test.py" (optional, for folders)
  - preserveStructure: "true" (optional, default: false)
```

**Response**:
```json
{
  "success": true,
  "message": "File test.py uploaded successfully",
  "path": "/Examples/Week1/homework/test.py",
  "project": "Local/sa9082"
}
```

**Example Use Cases**:
- Single file: Upload `test.py` to `Local/sa9082/Examples/`
- Folder structure: Upload `Week1/` folder with nested files

---

### 2. `/api/bulk-upload` (New)
**Purpose**: Upload files to multiple students simultaneously

**Request**:
```javascript
FormData:
  - file: File
  - targetStudents: "all" OR ["sa9082", "jd1234", ...]
  - commonFolder: "Examples"
  - subPath: "Week1" (optional)
  - filename: "lecture.py"
  - relativePath: "lecture.py" (optional)
  - preserveStructure: "true" (optional)
```

**Response**:
```json
{
  "success": true,
  "uploaded_to": 58,
  "total_students": 60,
  "failed_students": ["test_student1", "test_student2"],
  "file_path": "/Examples/Week1/lecture.py",
  "warning": "Failed to upload to 2 student(s)"
}
```

**Example Use Cases**:
- Upload lecture notes to all students: `Examples/Week1/`
- Upload assignment template to specific students

---

## Usage Examples

### Example 1: Upload Folder to Single Student
**Scenario**: Admin wants to upload "Week1" folder to student sa9082's Examples directory

**Steps**:
1. Open Import Files dialog
2. Select destination: `Local/sa9082/Examples`
3. Switch to "Folder" mode
4. Select "Week1" folder from computer
5. Click "Import"

**Result**:
```
Local/sa9082/Examples/
  └── Week1/
      ├── lecture.py
      ├── homework.py
      └── data/
          └── test.csv
```

---

### Example 2: Bulk Upload to All Students
**Scenario**: Professor wants to upload "Week2_Materials" to all students' Examples folder

**Steps**:
1. Open Bulk Upload dialog (admin-only)
2. Select "All Students" (60+ students)
3. Set destination: `Examples` folder
4. Optional: Add sub-path `Week2`
5. Switch to "Folder" mode
6. Select "Week2_Materials" folder
7. Click "Upload to 60 Student(s)"

**Result** (for each student):
```
Local/sa9082/Examples/Week2/Week2_Materials/...
Local/jd1234/Examples/Week2/Week2_Materials/...
... (all 60 students)
```

---

### Example 3: Upload to Specific Students
**Scenario**: Upload assignment only to students in Section A

**Steps**:
1. Open Bulk Upload dialog
2. Select "Specific Students"
3. Search and select: sa9082, jd1234, aas10176
4. Set destination: `Examples/Assignments`
5. Select files
6. Click "Upload to 3 Student(s)"

**Result**:
```
Local/sa9082/Examples/Assignments/assignment1.py
Local/jd1234/Examples/Assignments/assignment1.py
Local/aas10176/Examples/Assignments/assignment1.py
```

---

## Testing Guide

### Local Testing

1. **Start Backend** (in separate terminal):
   ```bash
   cd /home/sachinadlakha/on-campus/PythonIDE-Clean
   python server/server.py --port 10086
   ```

2. **Start Frontend** (in separate terminal):
   ```bash
   npm run dev
   ```

3. **Test Cases**:

   **Test 1: Single File Upload**
   - Login as admin (sl7927, sa9082, or et2434)
   - Navigate to any student's folder
   - Click "Import Files"
   - Upload a single .py file
   - Verify file appears in correct location

   **Test 2: Folder Upload (Single Student)**
   - Create test folder structure:
     ```
     TestFolder/
       ├── file1.py
       ├── subfolder/
       │   └── file2.py
     ```
   - Click "Import Files"
   - Switch to "Folder" mode
   - Select TestFolder
   - Verify structure is preserved

   **Test 3: Bulk Upload to All Students**
   - Open Bulk Upload dialog
   - Select "All Students"
   - Set destination: `Examples/Test`
   - Upload test file
   - Check multiple student directories to verify

   **Test 4: Folder Structure Preservation**
   - Upload nested folder with multiple levels
   - Verify all subdirectories are created
   - Verify file paths are correct

### AWS Production Testing

1. **Build and Deploy**:
   ```bash
   # Build Docker image with correct platform
   docker build --platform linux/amd64 -t pythonide-backend:latest .

   # Push to ECR
   aws ecr get-login-password --region us-east-2 | \
     docker login --username AWS --password-stdin \
     653306034507.dkr.ecr.us-east-2.amazonaws.com

   docker tag pythonide-backend:latest \
     653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:latest

   docker push 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:latest

   # Update ECS service
   aws ecs update-service \
     --cluster pythonide-cluster \
     --service pythonide-service \
     --force-new-deployment \
     --region us-east-2
   ```

2. **Verify EFS Mounting**:
   ```bash
   # Check ECS task logs
   aws logs tail /aws/ecs/pythonide --follow --region us-east-2

   # Look for:
   # ✓ File storage initialized at: /mnt/efs/pythonide-data
   # ✓ Storage type: AWS EFS
   ```

3. **Test Upload**:
   - Access production URL
   - Login as admin
   - Upload test folder
   - Verify files persist after container restart

4. **Verify Permissions**:
   - Login as student
   - Try to access own folder: ✅ Should work
   - Try to access another student's folder: ❌ Should be blocked
   - Login as professor
   - Access multiple student folders: ✅ Should work

---

## Security Considerations

### Admin-Only Endpoints
- `/api/upload-file` - Restricted to admin accounts only
- `/api/bulk-upload` - Restricted to admin accounts only

**Admin Accounts** ([upload_handler.py:57](server/handlers/upload_handler.py#L57)):
```python
admin_accounts = ["sl7927", "sa9082", "et2434", "admin_editor", "test_admin"]
```

### File Validation
- **Allowed Extensions**: `.py`, `.txt`, `.csv`, `.pdf`
- **Max File Size**: 10 MB per file
- **Path Sanitization**: Uses `os.path.basename()` to prevent directory traversal

### Permission Model
- Students can ONLY upload to their own `Local/{username}/` directory
- Admins can upload to ANY directory
- Upload handler validates session before processing

---

## Troubleshooting

### Issue 1: "Only admin users can upload files"
**Cause**: Current user is not in admin accounts list
**Solution**: Login with admin account (sl7927, sa9082, et2434)

### Issue 2: Folder structure not preserved
**Cause**: `preserveStructure` parameter not set
**Solution**: Ensure using "Folder" mode, not "Files" mode

### Issue 3: Files not persisting after deployment
**Cause**: EFS not mounted or wrong path
**Solution**: Check environment variable `IDE_DATA_PATH=/mnt/efs/pythonide-data`

### Issue 4: Bulk upload fails for some students
**Cause**: Student directory doesn't exist or permissions issue
**Solution**: Check `failed_students` in response, verify student accounts exist

### Issue 5: "No supported files found in folder"
**Cause**: Folder contains only non-supported file types
**Solution**: Ensure folder contains .py, .txt, .csv, or .pdf files

---

## Next Steps

### Recommended Enhancements

1. **Add Student List API**:
   ```python
   # /api/get-all-students endpoint
   # Returns list of all students for DialogBulkUpload
   ```

2. **Upload Progress Indicator**:
   - Show progress bar during bulk uploads
   - Display "X of Y files uploaded"

3. **Upload History Log**:
   - Track all bulk uploads by admins
   - Show timestamp, files, target students

4. **Email Notifications**:
   - Notify students when new materials are uploaded
   - Send summary to admin after bulk upload

5. **Folder Size Limits**:
   - Add total folder size validation
   - Prevent uploading folders > 100MB

6. **Undo/Rollback**:
   - Allow admins to undo recent bulk uploads
   - Soft-delete with recovery window

---

## Files Modified/Created

### Modified Files:
1. `src/components/element/pages/ide/dialog/DialogImportFile.vue` - Added folder upload
2. `server/handlers/upload_handler.py` - Enhanced for folder structure
3. `server/auth/user_manager_postgres.py` - Added get_all_students()
4. `server/server.py` - Registered bulk upload route

### New Files:
1. `server/handlers/bulk_upload_handler.py` - Bulk upload endpoint
2. `src/components/element/pages/ide/dialog/DialogBulkUpload.vue` - Bulk upload UI
3. `src/composables/useFileUpload.js` - Reusable upload logic

---

## Database Queries

### Get All Students:
```sql
SELECT username, full_name, email
FROM users
WHERE role = 'student'
ORDER BY username
```

---

## Environment Variables

### Local Development:
```bash
IDE_DATA_PATH=/tmp/pythonide-data
```

### AWS Production:
```bash
IDE_DATA_PATH=/mnt/efs/pythonide-data
DATABASE_URL=postgresql://pythonide_admin:...@pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432/pythonide
```

---

## Deployment Checklist

- [ ] Code merged to `main` branch
- [ ] Frontend built: `npm run build`
- [ ] Docker image built with `--platform linux/amd64`
- [ ] Image pushed to ECR
- [ ] ECS service updated
- [ ] EFS mount verified in logs
- [ ] Test upload in production
- [ ] Verify folder structure preservation
- [ ] Test bulk upload to all students
- [ ] Verify permissions (student vs admin)

---

## Contact & Support

**Implementation Date**: January 2025
**Implemented By**: Claude (Sonnet 4.5)
**Project Owner**: Sachin Adlakha

For issues or questions:
- Check CLAUDE.md for project context
- Review logs: `aws logs tail /aws/ecs/pythonide --follow`
- Verify EFS: Check `/mnt/efs/pythonide-data` exists in container
