# Git Best Practices for PythonIDE-Clean

## 🎯 Overview

This document outlines the best practices and quality checks enforced when pushing code to any branch in the PythonIDE-Clean repository.

## 🔐 Critical Security Concerns

### 1. **Never Commit Secrets or Credentials**
   - ❌ Database passwords
   - ❌ API keys (AWS, third-party services)
   - ❌ Session secrets
   - ❌ Student personal information
   - ❌ `.env` files with real credentials

   ✅ **Always use:**
   - `.env.example` for documenting required environment variables
   - GitHub Secrets for CI/CD credentials
   - AWS Secrets Manager for production secrets

### 2. **Authentication & Session Security**
   - ✅ All passwords must use bcrypt hashing
   - ✅ Session tokens must be validated on every WebSocket message
   - ✅ Single-session enforcement must be active (database-level)
   - ✅ Auto-logout after 1 hour of inactivity
   - ✅ Activity tracking on all user interactions

### 3. **File Storage Security**
   - ✅ All file paths must be validated to prevent directory traversal attacks
   - ✅ User files must be isolated to `Local/{username}/` directories
   - ✅ No direct user input to `open()`, `os.path.join()`, or file operations
   - ✅ Professors can view all student directories; students cannot cross-access

### 4. **WebSocket Security**
   - ✅ All WebSocket connections must be authenticated before processing commands
   - ✅ Rate limiting must be enforced to prevent abuse
   - ✅ Invalid authentication attempts must close the connection immediately
   - ✅ Activity tracking must update on every message

## 🧪 Automated CI/CD Checks

### What Runs on Every Non-Main Branch Push:

#### **Python Code Quality**
1. **Syntax Validation** - All Python files compile without errors
2. **Flake8 Linting** - Code style and quality checks (max line length: 120)
3. **Black Formatting** - Consistent code formatting (non-blocking)
4. **isort** - Organized import statements (non-blocking)
5. **Pylint** - Advanced code quality analysis (score ≥ 7.0, non-blocking)

#### **Security Scans**
1. **Bandit** - Python security vulnerability scanner (HIGH/CRITICAL severity)
2. **Safety** - Python dependency vulnerability checker (non-blocking)
3. **Docker Trivy Scan** - Container image vulnerability scanner (non-blocking)
4. **Directory Traversal Check** - Pattern-based security audit
5. **Password Security Verification** - Confirms bcrypt usage
6. **WebSocket Authentication Audit** - Verifies authentication flow

#### **Database & Infrastructure**
1. **Database Schema Validation** - Verifies tables and columns exist
2. **Migration Idempotency Check** - Ensures migrations can run multiple times safely
3. **Session Table Validation** - Confirms `last_activity` column exists
4. **Circular Import Detection** - Prevents import dependency loops

#### **Frontend Quality**
1. **ESLint** - JavaScript/Vue code linting (max 50 warnings, non-blocking)
2. **Build Test** - Ensures `npm run build` succeeds
3. **Dist Validation** - Confirms frontend artifacts are generated

#### **Docker & Deployment**
1. **Docker Build Test** - Validates Dockerfile builds successfully for linux/amd64
2. **Platform Check** - Ensures AWS ECS compatibility

#### **Configuration & Documentation**
1. **Environment Variable Documentation** - All required vars in `.env.example`
2. **README.md Exists** - Project documentation present
3. **CLAUDE.md Exists** - AI context documentation present

### What Runs on Main Branch Push:
All of the above **PLUS** automatic deployment to AWS ECS production environment.

## ✅ Pre-Commit Checklist (Before `git push`)

### **Every Developer Should Verify:**

1. **Code Compiles**
   ```bash
   cd server
   python -m py_compile $(find . -name "*.py" -not -path "./venv/*")
   ```

2. **No Syntax Errors**
   ```bash
   cd server
   python -c "import server; import auth.user_manager_postgres; import handlers.authenticated_ws_handler"
   ```

3. **Frontend Builds**
   ```bash
   npm run build
   ```

4. **No Secrets in Code**
   ```bash
   # Check for common patterns
   git diff | grep -E "(password|secret|key|token)" || echo "No secrets found"
   ```

5. **Database Migration Safe**
   - If you added database columns, ensure migration is idempotent
   - Check for `IF NOT EXISTS` or column existence checks

6. **WebSocket Changes Maintain Security**
   - Authentication still enforced?
   - Activity tracking still active?
   - Single-session enforcement intact?

7. **Student Data Privacy**
   - No student usernames/emails in code or logs
   - File isolation still working?
   - Permission checks in place?

## 🚨 What Will Block Your Push (CI/CD Failures)

### **Hard Failures (Build Stops):**
1. Python syntax errors
2. Frontend build failure
3. Docker build failure
4. Missing database tables or columns
5. Missing authentication checks in WebSocket handler
6. Missing password hashing (bcrypt)
7. Missing required configuration files (.env.example, Dockerfile, requirements.txt)

### **Warnings (Non-Blocking):**
1. Flake8 linting issues
2. Black formatting issues
3. Import sorting issues
4. Pylint score below 7.0
5. ESLint warnings (up to 50 allowed)
6. Docker security vulnerabilities
7. Python dependency vulnerabilities

## 📋 Branch Strategy

### **Main Branch**
- Production-ready code only
- Auto-deploys to AWS ECS on every push
- All CI/CD checks must pass
- Requires PR review (recommended)

### **Feature Branches**
- `feat/feature-name` - New features
- `fix/bug-name` - Bug fixes
- `refactor/component-name` - Code refactoring
- `docs/topic` - Documentation updates

### **Testing Branches**
- `test/scenario-name` - Testing environments
- Does not deploy to production

## 🔧 Local Development Best Practices

### **1. Keep Dependencies Updated**
```bash
# Check for outdated packages
cd server
pip list --outdated

# Frontend dependencies
npm outdated
```

### **2. Test Locally Before Pushing**
```bash
# Run local linting
cd server
flake8 . --max-line-length=120 --exclude=venv,data

# Test frontend
npm run lint
npm run build

# Test Docker build
docker build --platform linux/amd64 -t pythonide-test:latest .
```

### **3. Use Virtual Environments**
```bash
cd server
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### **4. Keep .gitignore Updated**
Never commit:
- `venv/`, `node_modules/`, `__pycache__/`
- `.env` (use `.env.example` instead)
- `*.pyc`, `*.pyo`, `.DS_Store`
- `server/data/` (local database)
- IDE-specific files (`.vscode/`, `.idea/`)

## 🎓 Educational IDE-Specific Concerns

### **1. Student Code Execution Safety**
- ✅ Resource limits enforced (CPU, memory, time)
- ✅ Process cleanup every 5 minutes
- ✅ Max 20 concurrent user processes
- ✅ Max 1 hour process age (2 hours for REPL)
- ✅ Sandboxed file system access

### **2. Academic Integrity**
- ✅ Copy/paste restrictions for students (not professors)
- ✅ Content fingerprinting system active
- ✅ Audit logs for suspicious activity

### **3. Scalability Considerations**
- ✅ Database connection pooling (5-20 connections)
- ✅ WebSocket keepalive for connection stability
- ✅ Auto-scaling on AWS (2-6 tasks, CPU target 45%)
- ✅ Supports 60+ concurrent students

### **4. Data Privacy**
- ✅ Student files isolated per username
- ✅ Professors can grade, students cannot cross-access
- ✅ Session tokens expire after 24 hours
- ✅ Auto-logout after 1 hour inactivity

## 🚀 Deployment Workflow

### **Feature Development Flow:**
```
1. Create feature branch: git checkout -b feat/my-feature
2. Make changes and test locally
3. Commit: git commit -m "feat: add new feature"
4. Push: git push origin feat/my-feature
5. CI/CD runs tests (no deployment)
6. Fix any failures
7. Create PR to main
8. After review, merge to main
9. Main branch auto-deploys to AWS
```

### **Hotfix Flow:**
```
1. Create fix branch: git checkout -b fix/critical-bug
2. Make minimal fix
3. Test thoroughly
4. Push and create PR
5. Fast-track review
6. Merge to main
7. Monitor AWS deployment
```

## 🐛 Common Issues & Solutions

### **Issue: CI/CD fails on Python syntax**
**Solution:** Run `python -m py_compile file.py` locally before pushing

### **Issue: Frontend build fails**
**Solution:** Delete `node_modules/` and `package-lock.json`, then `npm install`

### **Issue: Docker build fails**
**Solution:** Check Dockerfile syntax, ensure all COPY paths exist

### **Issue: Database migration fails**
**Solution:** Make migrations idempotent with `IF NOT EXISTS` or column checks

### **Issue: WebSocket authentication check fails**
**Solution:** Ensure `self.authenticated`, `invalidate_other_sessions`, and `update_session_activity` exist in code

## 📞 Getting Help

### **CI/CD Pipeline Issues**
- Check GitHub Actions logs: `.github/workflows/development-test.yml`
- Review error messages in Actions tab
- Search for similar issues in commit history

### **Security Concerns**
- Review security scan reports (Bandit, Safety)
- Check AWS CloudWatch logs for runtime issues
- Audit WebSocket authentication flow

### **Database Issues**
- Test migrations locally with SQLite first
- Check PostgreSQL logs on AWS RDS
- Verify connection pooling settings

## 📊 Metrics to Monitor

### **Before Every Main Branch Merge:**
- [ ] All CI/CD checks passing
- [ ] No new security vulnerabilities introduced
- [ ] Database migrations tested locally
- [ ] Frontend builds successfully
- [ ] Docker image builds for linux/amd64
- [ ] No secrets in code
- [ ] Documentation updated if needed

### **After Deployment to Production:**
- [ ] AWS ECS service healthy
- [ ] All tasks running (min 2)
- [ ] Auto-scaling configured correctly
- [ ] WebSocket connections stable
- [ ] Database connection pool healthy
- [ ] No error spikes in CloudWatch

---

## 🎯 Summary

**Key Takeaway:** The CI/CD pipeline is designed to catch issues before they reach production. If a check fails, fix it before merging to main. All checks exist for security, reliability, and educational integrity reasons.

**Remember:** This is an educational platform serving 60+ students. Stability and security are paramount.

**Questions?** Check CLAUDE.md for full project context and architecture details.
