# PythonIDE-Clean Project Context

## Project Overview
PythonIDE-Clean is a web-based Python IDE designed for educational use at a college. It supports 60+ concurrent students, allowing them to write, execute, and submit Python code for assignments and tests.

## Current Status (Updated: December 2024)

### ✅ Implemented Features:
1. **User authentication** - Login system with bcrypt password hashing
2. **File isolation** - Each student has `Local/{username}/` folder
3. **PostgreSQL database** - Migrated from SQLite for scalability
4. **Authenticated WebSockets** - Secure real-time connections
5. **Role-based permissions** - Student vs Professor access control
6. **Cloud deployment** - Railway platform with automatic scaling
7. **Session management** - Token-based authentication
8. **File synchronization** - Database tracks file metadata
9. **Hybrid REPL System** - Scripts transition to REPL with variable persistence

### ⚠️ Remaining Issues:
1. **Resource limits** - Need CPU/memory limits per execution
2. **Rate limiting** - No request throttling implemented
3. **Process cleanup** - Abandoned processes not cleaned automatically
4. **Monitoring** - Basic logging only, no APM integration
5. **Backups** - Manual process, not automated

### Current Capacity:
- **With PostgreSQL: 60+ concurrent users** (previously 5-10 with SQLite)
- Tested up to 20 concurrent users successfully

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

### Production Environment (Railway):
- **Platform**: Railway.app cloud hosting
- **Database**: PostgreSQL (managed by Railway)
- **URL**: Accessible via Railway-generated domain
- **Scaling**: Automatic based on load
- **Cost**: $0-20/month on free tier

### Environment Variables:
```bash
DATABASE_URL=postgresql://...  # Auto-set by Railway
PORT=8080                       # Auto-set by Railway
IDE_SECRET_KEY=<secure-key>
MAX_CONCURRENT_EXECUTIONS=60
EXECUTION_TIMEOUT=30
MEMORY_LIMIT_MB=128
```

### Deployment Process:
```bash
# Deploy to Railway
railway up

# Initialize users
railway run python server/migrations/create_users.py

# Monitor logs
railway logs
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