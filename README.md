# PythonIDE-Clean: Educational Python IDE Platform

> A secure, multi-user web-based Python IDE designed for educational institutions
> Built with Vue3 + Python3.10 + Tornado6.1 + SQLite
> Supporting 60+ concurrent students with isolated workspaces

## 🎯 Project Overview

PythonIDE-Clean is a comprehensive web-based Python development environment specifically designed for educational use in colleges and universities. It provides a secure, isolated coding environment where students can write, execute, and submit Python assignments while professors can manage course materials and grade submissions.

## ✨ Key Features

### Core IDE Functionality
- **Multi-file code editor** with syntax highlighting and auto-completion
- **Real-time Python code execution** with output streaming
- **File management system** - Create, read, update, delete files and folders
- **Multiple file type support**:
  - Python files (.py) with syntax highlighting
  - Markdown files (.md) with live preview
  - CSV files with built-in viewer
  - Media files (images, PDFs) with preview support
- **Advanced editor features**:
  - Find and replace functionality
  - Code tabs for multiple file editing
  - Keyboard shortcuts
  - Customizable settings
  - Word wrap toggle

### Security & Multi-User Support
- **User authentication system** with secure session management
- **Role-based access control** (Students and Professors)
- **Isolated user workspaces** - Each student has their own directory
- **File permission system** preventing unauthorized access
- **Resource-limited code execution** (CPU, memory, timeout limits)
- **SQLite database** for user management and file metadata

### Educational Features
- **Assignment submission system** with unique submission IDs
- **Professor dashboard** for viewing all student work
- **Grading interface** for professors
- **Lecture notes distribution** (read-only for students)
- **Organized directory structure**:
  ```
  /projects/ide/
  ├── Local/           # Student personal workspaces
  │   ├── sa9082/      # Individual student directory
  │   └── jd1234/      # Another student's directory
  ├── Lecture Notes/   # Professor uploads, student read-only
  ├── Assignments/     # Assignment materials and submissions
  └── Tests/          # Test materials and submissions
  ```

### UI Components
- **Split-pane interface** with resizable panels
- **Project tree navigation** with VSCode-style icons
- **Interactive console** with REPL support
- **Unified console** for output management
- **Top menu** with common actions
- **Dialogs** for file operations, uploads, and settings

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Vue 3, Vuex, CodeMirror, Element Plus UI
- **Backend**: Python 3.10, Tornado WebSocket Server
- **Database**: SQLite for user management and metadata
- **Authentication**: bcrypt password hashing, session-based auth
- **File Storage**: Local filesystem with permission validation

### System Requirements
- **Capacity**: Supports 60+ concurrent users
- **Performance**: <500ms response time for file operations
- **Security**: Directory-based isolation, resource limits
- **Reliability**: Transaction-based file operations, automatic cleanup

## 🚀 Installation & Setup

### Prerequisites
- Node.js 16.13.2+
- npm 8.1.2+
- Python 3.10+
- SQLite 3

### Quick Start

#### 1. Clone and Install Dependencies
```bash
# Clone the repository
git clone <repository-url>
cd PythonIDE-Clean

# Install frontend dependencies
npm install

# Install backend dependencies
cd server
pip install -r requirements.txt
cd ..
```

#### 2. Database Setup
```bash
# Initialize database schema
cd server
sqlite3 ide.db < migrations/001_initial_schema.sql

# Create initial users
python migrations/create_users.py

# Set up directory structure
python migrations/setup_directories.py
cd ..
```

#### 3. Run Development Environment
```bash
# Terminal 1: Start backend server
cd server
python server.py --port 10086

# Terminal 2: Start frontend development server
npm run serve

# Access the application
# Frontend: http://localhost:8080
# Backend: http://localhost:10086
```

#### 4. Production Build
```bash
# Build frontend for production
npm run build

# The built files will be in the dist/ directory
# Backend will automatically serve these files

# Run production server
cd server
python server.py --port 10086

# Access at: http://localhost:10086
```

## 👥 User Management

### Default Credentials
- **Professor**: username: `professor`, password: `ChangeMeASAP2024!`
- **Students**: username: `{student_id}`, password: `{student_id}2024`

### User Roles & Permissions
| Role | Permissions |
|------|------------|
| **Student** | • Full access to personal workspace (`Local/{username}/`)<br>• Read-only access to Lecture Notes<br>• Submit assignments in designated folders<br>• Execute Python code with resource limits |
| **Professor** | • Full access to all directories<br>• Upload lecture materials<br>• View all student submissions<br>• Grade assignments with feedback |

## 📁 Project Structure

```
PythonIDE-Clean/
├── src/                    # Frontend source code
│   ├── components/         # Vue components
│   │   └── element/
│   │       └── pages/ide/  # IDE components
│   ├── store/             # Vuex state management
│   └── assets/            # Icons, styles, themes
├── server/                # Backend source code
│   ├── auth/             # Authentication system
│   ├── command/          # Command processors
│   ├── handlers/         # WebSocket handlers
│   ├── migrations/       # Database migrations
│   └── projects/ide/     # User file storage
├── dist/                 # Production build output
└── public/               # Static assets
```

## 🔒 Security Features

- **Authentication**: Session-based with bcrypt password hashing
- **Authorization**: Role-based access control (RBAC)
- **File Isolation**: Directory-based permissions
- **Path Validation**: Prevents directory traversal attacks
- **Resource Limits**: 
  - Execution timeout: 30 seconds
  - Memory limit: 128MB per execution
  - File size limit: 10MB
- **WebSocket Security**: Authenticated connections only

## 📊 Performance Specifications

| Metric | Target | Current |
|--------|--------|---------|
| Concurrent Users | 60+ | ✅ Supported |
| File Operation Response | <500ms | ✅ Achieved |
| Code Execution Timeout | 30s max | ✅ Enforced |
| Memory per Execution | 128MB | ✅ Limited |
| WebSocket Connections | 100+ | ✅ Stable |

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/

# Run load test (60 concurrent users)
python tests/load_test.py --users 60

# Test authentication flow
python tests/test_auth.py

# Test file permissions
python tests/test_permissions.py
```

## 📝 Migration from Single-User

Detailed migration plan available in `MIGRATION_PLAN.md`. Key phases:
1. **Phase 1**: Database & Authentication setup
2. **Phase 2**: File system migration
3. **Phase 3**: Backend updates for multi-user
4. **Phase 4**: Frontend authentication integration
5. **Phase 5**: Testing & validation
6. **Phase 6**: Production deployment

## 🔧 Configuration

### Environment Variables
```bash
# Server configuration
IDE_PORT=10086
IDE_HOST=0.0.0.0
IDE_ENV=production

# Database
DATABASE_PATH=/server/ide.db

# Security
SESSION_TIMEOUT=86400
MAX_FILE_SIZE=10485760
MAX_EXECUTION_TIME=30
```

## 🚦 Monitoring & Maintenance

### Health Checks
```bash
# Check server status
curl http://localhost:10086/health

# View active sessions
sqlite3 server/ide.db "SELECT * FROM sessions WHERE expires_at > datetime('now');"

# Monitor WebSocket connections
python server/monitor.py
```

### Backup & Recovery
```bash
# Backup database and files
tar -czf backup_$(date +%Y%m%d).tar.gz server/projects/ide/ server/ide.db

# Restore from backup
tar -xzf backup_20240101.tar.gz
```

## 📚 Documentation

- `CLAUDE.md` - Detailed project context and requirements
- `MIGRATION_PLAN.md` - Step-by-step migration guide
- `P5JS_EDITOR_COMPLETE_ANALYSIS.md` - Reference architecture analysis

## 🤝 Contributing

This project is designed for educational use at colleges. For bug reports or feature requests, please contact the development team.

## 📄 License

This project is proprietary software for educational institutions. All rights reserved.

## 👨‍💻 Contact

**Project Lead**: Sachin Adlakha  
**Target Deployment**: College Internal Server  
**User Base**: 60+ students, 2+ professors  
**Course**: Introductory Python Programming
