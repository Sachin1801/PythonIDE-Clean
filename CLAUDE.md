# PythonIDE-Clean Project Context

## Project Overview
PythonIDE-Clean is a web-based Python IDE designed for educational use at a college. It supports 60+ concurrent students, allowing them to write, execute, and submit Python code for assignments and tests.

## Current Status (Updated: 25 September 2025)

### ✅ Implemented Features:
1. **User authentication** - Login system with bcrypt password hashing
2. **File isolation** - Each student has `Local/{username}/` folder (60+ students) + test accounts (admin_viewer, test_student)
3. **PostgreSQL database** - AWS RDS PostgreSQL for production
4. **Authenticated WebSockets** - Secure real-time connections
5. **Role-based permissions** - Student vs Professor access control (admin accounts: sl7927, sa9082, et2434, admin_editor, test_admin)
6. **AWS deployment** - ECS Fargate with EFS persistent storage
7. **Session management** - Token-based authentication
8. **File synchronization** - Database tracks file metadata
9. **Hybrid REPL System** - Scripts transition to REPL with variable persistence
10. **Admin permissions** - Professors can see all student directories in Local/
11. **Universal keyboard shortcuts** - Ctrl+C/V works across all platforms (including Mac) in modals and IDE
12. **Academic integrity controls** - Copy/paste restrictions prevent students from pasting external content

### ✅ Production Status:
- **AWS ECS Service**: Running and stable
- **GitHub Actions CI/CD**: Automated deployment from main branch only
- **Student Account Management**: 60+ students + test account system
- **Security**: Cleaned repository with no exposed credentials

### 🎯 Working Configuration:
- **Account ID**: 653306034507
- **Region**: us-east-2
- **EFS ID**: fs-0ba3b6fecab24774a
- **RDS Endpoint**: pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com
- **Load Balancer**: pythonide-alb-456687384.us-east-2.elb.amazonaws.com
- **Student Count**: 60+ active students (recent additions: aas10176, bh2854)
- **Database**: pythonide (AWS RDS PostgreSQL)

## Current Architecture

### Core Components:
1. **PostgreSQL Database** - User management, file metadata, permissions (AWS RDS hosted)
2. **Local Filesystem** - Actual file storage at `/mnt/efs/pythonide-data` (AWS EFS)
3. **Directory-based Isolation** - Each student gets `Local/{username}/` folder
4. **WebSocket + Auth** - Authenticated connections with session management
5. **Subprocess Execution** - Python execution (resource limits pending)
6. **AWS ECS Fargate** - Container hosting with auto-scaling
7. **Database Connection Pool** - 5-20 connections for concurrent access

### Directory Structure:
```
/mnt/efs/pythonide-data/
├── Local/
│   ├── sa9082/         # Student's personal workspace
│   ├── jd1234/         # Another student's workspace
│   └── ...             # 60+ student directories
├── Lecture Notes/      # Professor uploads, students read-only
```

### User Roles & Permissions:
- **Students:**
  - Full access: `Local/{username}/`
  - Read-only: `Lecture Notes/`
  
- **Professors:**
  - Full access to everything
  - Can view all student submissions
  - Can grade assignments

## Deployment & Infrastructure

### Production Environment (AWS):
- **Platform**: AWS ECS Fargate
- **Database**: AWS RDS PostgreSQL (pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com)
- **Storage**: AWS EFS (fs-0ba3b6fecab24774a) mounted at /mnt/efs/pythonide-data
- **Load Balancer**: pythonide-alb-456687384.us-east-2.elb.amazonaws.com
- **Region**: us-east-2
- **Container Registry**: ECR (653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend)
- **Status**: Infrastructure ready, service failing due to Docker image platform issues

### Environment Variables (AWS):
```bash
DATABASE_URL=postgresql://pythonide_admin:Sachinadlakha9082@pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432/pythonide
IDE_SECRET_KEY=@ok#N2q0%!F2zGUuC^rYvtY2Op#hkEWsMtBRDsk@5Bq7D8x#Y18kajwIrozM0YE6
IDE_DATA_PATH=/mnt/efs/pythonide-data
PORT=8080
MAX_CONCURRENT_EXECUTIONS=60
EXECUTION_TIMEOUT=30
MEMORY_LIMIT_MB=128
```

### Deployment Process (AWS):
**Automated via GitHub Actions:**
- Push to `main` branch triggers production deployment
- Feature branches run tests only (no deployment)
- Manual deployment available via `workflow_dispatch`

**Manual deployment (if needed):**
```bash
# Build with explicit platform
docker build --platform linux/amd64 -f Dockerfile -t pythonide-backend:latest .

# Push to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 653306034507.dkr.ecr.us-east-2.amazonaws.com
docker tag pythonide-backend:latest 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:latest
docker push 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:latest

# Update ECS service
aws ecs update-service --cluster pythonide-cluster --service pythonide-service --force-new-deployment --region us-east-2
```

## Hybrid REPL System

### Overview:
The IDE features a hybrid REPL (Read-Eval-Print-Loop) system that seamlessly transitions from script execution to interactive mode, similar to Python IDLE.

### Key Features:
- **Script-to-REPL Transition**: After a script completes execution, the console automatically enters REPL mode
- **Variable Persistence**: All variables, functions, and imports from the script remain available in REPL
- **Error Handling**: If script has errors, REPL does not open (clean failure)
- **Per-File Sessions**: Each file maintains its own REPL session; switching files closes the previous REPL
- **Empty REPL Mode**: Professors can open empty REPL for teaching via "Show REPL" menu option
- **History Navigation**: Up/Down arrows navigate command history in REPL mode

### Implementation:
- **Server**: `HybridREPLThread` in `/server/command/hybrid_repl_thread.py`
- **Client**: `HybridConsole.vue` component for unified script/REPL display
- **Permission-Aware**: Respects user directory permissions (`Local/{username}/`)

### Usage:
1. **Run Script → REPL**: Click Run on any Python file, script executes, then REPL opens with all variables
2. **Empty REPL**: Click "Show REPL" in View menu to open interactive Python without running a script
3. **File Context**: Each file's REPL maintains separate context; switching files resets REPL

## Keyboard Shortcuts & Academic Integrity

### Universal Keyboard Shortcuts
The IDE implements consistent keyboard shortcuts across all platforms (Windows, Mac, Linux):

**Implementation:**
- **Global keyboard handler**: Centralized shortcut management in `TwoHeaderMenu.vue`
- **Cross-platform consistency**: Uses `Ctrl+C/V` on all platforms (including Mac, not `Cmd+C/V`)
- **Context-aware behavior**: Allows native copy/paste in text input fields, custom behavior in code editor

**Supported Shortcuts:**
- **Copy/Cut/Paste**: `Ctrl+C/X/V` - Works in modals, IDE editor, REPL inputs
- **File Operations**: `Ctrl+S` (Save), `Ctrl+Shift+S` (Save As), `Ctrl+Alt+N` (New File), `Ctrl+O` (Open)
- **Edit Operations**: `Ctrl+Z/Y` (Undo/Redo), `Ctrl+A` (Select All), `Ctrl+F/H` (Find/Replace)
- **IDE Operations**: `F5` (Run Script), `Shift+F5` (Stop Script), `Ctrl+B` (Toggle Sidebar)

### Academic Integrity Controls

**Purpose**: Prevent students from copying code from external websites or applications while allowing legitimate IDE usage.

**Implementation:**
- **Content fingerprinting system** (`/src/utils/clipboardTracker.js`)
- **CodeMirror integration** with copy/paste validation
- **Role-based permissions** distinguishing students from professors

**How It Works:**
1. **Copy Tracking**: When students copy/cut text within the IDE (CodeMirror editor), content is hashed and stored as "allowed"
2. **Paste Validation**: When students attempt to paste, system checks if content hash exists in allowed list
3. **Restriction Enforcement**:
   - ✅ **Students**: Can paste only content previously copied within IDE
   - ✅ **Professors**: Can paste from anywhere (no restrictions)
   - ❌ **External Content**: Students see toast notification: "Cannot paste from external websites"

**Technical Details:**
```javascript
// Content fingerprinting with normalization
generateContentHash(content) {
  const normalized = content.trim().replace(/\s+/g, ' ');
  // Hash generation with length verification
}

// Role-based validation
validatePaste(content) {
  if (isProfessor()) return true;  // No restrictions
  if (isStudent()) return isContentAllowed(content);  // Check fingerprint
}
```

**Scope of Restrictions:**
- **Applies to**: CodeMirror editor (main Python coding area)
- **Does not apply to**: Modal text fields, REPL inputs, other text areas
- **Cross-file copying**: Students can copy from FileA.py and paste into FileB.py within IDE
- **No bypass protection**: Currently assumes students won't use DevTools (can be added later)

## Technical Stack

### Backend:
- **Python 3.11** with Tornado WebSocket server
- **PostgreSQL** for user data and file metadata (with connection pooling)
- **bcrypt** for password hashing
- **psycopg2** for PostgreSQL connectivity
- **subprocess** for code execution (resource limits pending)
- **python-dotenv** for environment configuration

### Frontend:
- **Vue 3** with Vuex state management
- **CodeMirror** for code editing
- **WebSocket** for real-time communication
- **Element Plus** UI components

### File Storage:
- **AWS EFS filesystem** at `/mnt/efs/pythonide-data/`
- **Persistent storage** across container restarts
- **PostgreSQL tracks metadata** (ownership, permissions, grades)
- **File synchronization** via `file_sync` module
- **Binary file support** for PDFs, images, CSVs

## Key Design Decisions

1. **Why PostgreSQL over SQLite?**
   - Handles 60+ concurrent users (SQLite limited to 5-10)
   - Connection pooling for better concurrency
   - AWS RDS provides managed PostgreSQL with automatic backups
   - Better performance under load
   - ACID transactions with proper locking

2. **Why AWS EFS over local storage?**
   - Persistent storage across container restarts
   - Automatic scaling and redundancy
   - Shared access for multiple container instances
   - Built-in backup and versioning
   - Integration with AWS security policies

3. **Why directory-based isolation?**
   - Simple permission model
   - Maps to familiar file system concepts
   - Easy for professors to understand/navigate
   - Natural organization for course materials

4. **Why AWS ECS Fargate over self-hosted?**
   - Zero server management
   - Automatic scaling based on demand
   - Built-in load balancing and SSL/HTTPS
   - Integration with AWS security and monitoring
   - Pay-per-use pricing model

## Implementation Guidelines

### Security Requirements:
- All file paths must be validated to prevent directory traversal
- User passwords must be hashed with bcrypt
- WebSocket connections must be authenticated
- Resource limits must be enforced on all code execution
- File operations must use transactions

### Performance Requirements:
- Support 60 concurrent users
- Code execution timeout: 30 seconds max
- Memory limit per execution: 128MB
- File size limit: 10MB
- Response time: <500ms for file operations

### Reliability Requirements:
- Graceful handling of WebSocket disconnections
- Automatic cleanup of abandoned processes
- Transaction-based file operations
- Daily automated backups
- Error logging and monitoring

## Common Commands

### Local Development:
```bash
# Install dependencies
pip install -r server/requirements.txt
npm install

# Build frontend
npm run build

# Start server locally
python server/server.py --port 10086
```

### AWS Deployment:
```bash
# Automated deployment via GitHub Actions
git push origin main  # Triggers production deployment

# Manual deployment (if needed)
aws ecs update-service --cluster pythonide-cluster --service pythonide-service --force-new-deployment --region us-east-2

# View container logs
aws logs tail /aws/ecs/pythonide --follow --region us-east-2

# Check service status
aws ecs describe-services --cluster pythonide-cluster --services pythonide-service --region us-east-2
```

### Database Management:
```bash
# Connect to AWS RDS PostgreSQL
psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com -U pythonide_admin -d pythonide

# Backup database
pg_dump -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com -U pythonide_admin pythonide > backup.sql

# Create users in PostgreSQL
python server/migrations/create_users.py
```

## FAQ for Future Development

**Q: Why not use Supabase/Firebase?**
A: College requirement to keep all data on-premises. No external services allowed.

**Q: Can we add more features later?**
A: Yes, architecture supports adding features like:
- Real-time collaboration
- Version control integration
- Advanced grading rubrics
- Plagiarism detection

**Q: What about scaling beyond 60 users?**
A: Current architecture with AWS can handle ~200 users. Beyond that:
- Add Redis for session caching
- Implement horizontal scaling with multiple ECS tasks
- Add CloudFront CDN for static assets
- Consider microservices architecture with AWS Lambda

**Q: How do we handle exam mode?**
A: Can implement:
- Time-limited sessions
- Restricted internet access
- Locked assignment submissions
- Proctoring integration

## Contact & Documentation

- **Project Lead:** Sachin Adlakha
- **Deployment Platform:** AWS ECS Fargate
- **Database:** PostgreSQL (AWS RDS managed)
- **User Base:** 60+ students + admin accounts
- **Course:** Introductory Python Programming
- **Status:** Production-ready with AWS infrastructure

## Next Steps

1. ✅ ~~Implement user authentication system~~ (DONE)
2. ✅ ~~Add directory-based file isolation~~ (DONE)
3. ✅ ~~Deploy to AWS with PostgreSQL~~ (DONE)
4. ✅ ~~Implement Hybrid REPL System~~ (DONE)
5. ✅ ~~Universal keyboard shortcuts~~ (DONE)
6. ✅ ~~Academic integrity copy/paste controls~~ (DONE)
7. ⏳ Add resource limits for code execution
8. ⏳ Implement rate limiting
9. ⏳ Create professor grading interface
10. ⏳ Add automated backups
11. ⏳ Implement monitoring and alerting

---

*This document should be read by any AI assistant or developer working on this project to understand the full context and requirements.*