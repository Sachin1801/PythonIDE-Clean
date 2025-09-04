# PythonIDE-Clean Project Context

## Project Overview
PythonIDE-Clean is a web-based Python IDE designed for educational use at a college. It supports 60+ concurrent students, allowing them to write, execute, and submit Python code for assignments and tests.

## Current Status (Updated: January 2025)

### ✅ Implemented Features:
1. **User authentication** - Login system with bcrypt password hashing
2. **File isolation** - Each student has `Local/{username}/` folder (41 students)
3. **PostgreSQL database** - AWS RDS PostgreSQL for production
4. **Authenticated WebSockets** - Secure real-time connections
5. **Role-based permissions** - Student vs Professor access control (3 admin accounts: sl7927, sa9082, et2434)
6. **AWS deployment** - ECS Fargate with EFS persistent storage
7. **Session management** - Token-based authentication
8. **File synchronization** - Database tracks file metadata
9. **Hybrid REPL System** - Scripts transition to REPL with variable persistence
10. **Admin permissions** - Professors can see all student directories in Local/

### 🚨 Current Deployment Issues:
1. **Docker Platform Mismatch** - Image built with wrong platform manifest for AWS Fargate
2. **Docker Credential Issues** - Cannot rebuild image locally due to credential problems
3. **Service Down** - ECS tasks failing to start due to platform incompatibility

### 🎯 Working Configuration:
- **Account ID**: 653306034507
- **Region**: us-east-2
- **EFS ID**: fs-0ba3b6fecab24774a
- **RDS Endpoint**: pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com
- **Load Balancer**: pythonide-alb-456687384.us-east-2.elb.amazonaws.com
- **Student Count**: 41 directories (all admin accounts present)
- **Database**: pythonide-db (corrected name)

### Current Capacity:
- **Target**: 60+ concurrent users on AWS ECS Fargate
- **Status**: Service configured but not running due to Docker image issues

## Current Architecture

### Core Components:
1. **PostgreSQL Database** - User management, file metadata, permissions (Railway-hosted)
2. **Local Filesystem** - Actual file storage at `/server/projects/ide/`
3. **Directory-based Isolation** - Each student gets `Local/{username}/` folder
4. **WebSocket + Auth** - Authenticated connections with session management
5. **Subprocess Execution** - Python execution (resource limits pending)
6. **Railway Platform** - Cloud hosting with automatic scaling
7. **Database Connection Pool** - 5-20 connections for concurrent access

### Directory Structure:
```
/server/projects/ide/
├── Local/
│   ├── sa9082/         # Student's personal workspace
│   ├── jd1234/         # Another student's workspace
│   └── ...
├── Lecture Notes/      # Professor uploads, students read-only
├── Assignments/        # Assignment descriptions and submissions
└── Tests/             # Test descriptions and submissions
```

### User Roles & Permissions:
- **Students:**
  - Full access: `Local/{username}/`
  - Read-only: `Lecture Notes/`
  - Write own files by students but assignment and test material uploaded by professor which is read only for students: `Assignments/`, `Tests/`
  
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
DATABASE_URL=postgresql://pythonide_admin:Sachinadlakha9082@pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432/pythonide-db
IDE_SECRET_KEY=@ok#N2q0%!F2zGUuC^rYvtY2Op#hkEWsMtBRDsk@5Bq7D8x#Y18kajwIrozM0YE6
IDE_DATA_PATH=/mnt/efs/pythonide-data
PORT=8080
MAX_CONCURRENT_EXECUTIONS=60
EXECUTION_TIMEOUT=30
MEMORY_LIMIT_MB=128
```

### Deployment Process (AWS):
```bash
# Build and deploy (currently failing due to platform issues)
./deploy-aws.sh

# Alternative: Build with explicit platform
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
- **Local filesystem** at `/server/projects/ide/`
- **No external storage needed** (no S3, no cloud)
- **PostgreSQL tracks metadata** (ownership, permissions, grades)
- **File synchronization** via `file_sync` module
- **Binary file support** for PDFs, images, CSVs

## Key Design Decisions

1. **Why PostgreSQL over SQLite?** (Updated)
   - Handles 60+ concurrent users (SQLite limited to 5-10)
   - Connection pooling for better concurrency
   - Railway provides managed PostgreSQL
   - Better performance under load
   - ACID transactions with proper locking

2. **Why local files over cloud storage?**
   - Already have server infrastructure
   - No external service costs
   - Fast file access (no network latency)
   - Simple deployment for college environment

3. **Why directory-based isolation?**
   - Simple permission model
   - Maps to familiar file system concepts
   - Easy for professors to understand/navigate
   - Natural organization for course materials

4. **Why Railway over self-hosted?**
   - Zero infrastructure management
   - Automatic SSL/HTTPS
   - Built-in PostgreSQL
   - Easy GitHub integration
   - Automatic deployments
   - Cost-effective for education ($0-20/month)

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

### Railway Deployment:
```bash
# Deploy to Railway
railway up

# Create users in PostgreSQL
railway run python server/migrations/create_users.py

# View logs
railway logs

# Get deployment URL
railway domain
```

### Database Management:
```bash
# Connect to PostgreSQL
railway run psql $DATABASE_URL

# Backup database
railway run pg_dump $DATABASE_URL > backup.sql
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
A: Current architecture with PostgreSQL can handle ~100 users. Beyond that:
- Add Redis for session caching
- Implement horizontal scaling on Railway
- Add CDN for static assets
- Consider microservices architecture

**Q: How do we handle exam mode?**
A: Can implement:
- Time-limited sessions
- Restricted internet access
- Locked assignment submissions
- Proctoring integration

## Contact & Documentation

- **Project Lead:** Sachin Adlakha
- **Deployment Platform:** Railway.app cloud
- **Database:** PostgreSQL (Railway-managed)
- **User Base:** 60 students + 1-2 professors
- **Course:** Introductory Python Programming
- **Status:** Production-ready with PostgreSQL

## Next Steps

1. ✅ ~~Implement user authentication system~~ (DONE)
2. ✅ ~~Add directory-based file isolation~~ (DONE)
3. ✅ ~~Deploy to Railway with PostgreSQL~~ (DONE)
4. ✅ ~~Implement Hybrid REPL System~~ (DONE)
5. ⏳ Add resource limits for code execution
6. ⏳ Implement rate limiting
7. ⏳ Create professor grading interface
8. ⏳ Add automated backups
9. ⏳ Implement monitoring and alerting

---

*This document should be read by any AI assistant or developer working on this project to understand the full context and requirements.*