# 🚀 Safe Push Guide - Exam Environment Changes

## Current Status

**Branch**: `staging` ✅
**CI/CD Setup**: ✅ Safe to push

---

## 🔒 CI/CD Configuration Analysis

### Your GitHub Actions Workflows:

| Workflow | Triggers On | Deploys To | Production Impact |
|----------|-------------|------------|-------------------|
| `deploy-aws-staging.yml` | `staging` branch | `pythonide-staging-service` | ❌ None |
| `deploy-aws.yml` | `main` branch | `pythonide-service` | ⚠️ **Production** |
| `development-test.yml` | Pull requests | Tests only | ❌ None |

### Your Deployed Services:

| Service | Environment | Auto-Deploy | Current Status |
|---------|-------------|-------------|----------------|
| `pythonide-service` | **Production Main IDE** | ✅ Yes (main branch) | Running |
| `pythonide-staging-service` | Staging/Testing | ✅ Yes (staging branch) | Running |
| `pythonide-exam-task-service` | **Production Exam IDE** | ❌ **Manual only** | Running |

---

## ✅ SAFE: Pushing to Staging Branch

**You're currently on `staging` branch - SAFE to push!**

When you push to `staging`:
- ✅ Deploys to `pythonide-staging-service` (separate test environment)
- ✅ Does NOT affect `pythonide-service` (main production IDE)
- ✅ Does NOT affect `pythonide-exam-task-service` (exam environment)
- ✅ No risk to production users

### What Will Happen:
1. GitHub Actions workflow `deploy-aws-staging.yml` will trigger
2. Builds Docker image with tag `staging-<commit-hash>`
3. Deploys to `pythonide-staging-service` only
4. You can test changes in staging before merging to main

---

## 📋 Step-by-Step: Safe Push to Staging

### Step 1: Review Changes
```bash
# See what's changed
git status

# See what files will be committed
git diff --name-status
```

### Step 2: Add Files for Commit
```bash
# Add new exam environment files
git add server/init_exam_users.py
git add server/handlers/lockdown_handler.py
git add docker-compose.exam.yml
git add deployment/ecs-task-definition-exam-fixed.json
git add deployment/setup-exam-database.sql
git add deployment/EXAM_ENVIRONMENT_WORKING.md
git add deployment/ROUTING_CONFIGURATION.md

# Add documentation
git add docs/EXAM_ENVIRONMENT_GUIDE.md
git add ROOT_CLEANUP_GUIDE.md
git add SAFE_PUSH_GUIDE.md

# Add CloudFront config (reference)
git add cloudfront-config.json

# Add modified files
git add .gitignore
git add server/command/hybrid_repl_thread.py

# Add deleted cleanup files
git add -u  # This stages all deletions
```

### Step 3: Commit Changes
```bash
git commit -m "feat: Add exam environment with complete isolation

- Add separate exam IDE environment (pythonide-exam-task-service)
- Create init_exam_users.py script for 41 exam students
- Add lockdown handler for optional main IDE blocking
- Configure subdomain routing (exam.pythonide-classroom.tech)
- Add comprehensive exam environment documentation
- Clean up outdated deployment and test files

Exam environment features:
- Separate database (pythonide_exam)
- Separate EFS storage path (/mnt/efs/pythonide-data-exam)
- 41 student accounts with random 5-char passwords
- 3 professor accounts for monitoring
- Complete isolation from main IDE

Deployment: Manual deployment to pythonide-exam-task-service (not auto-deployed)

🤖 Generated with Claude Code
https://claude.com/claude-code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 4: Push to Staging
```bash
# Push to staging branch
git push origin staging
```

### Step 5: Monitor Deployment
```bash
# Watch the GitHub Actions workflow
# Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/actions

# Or check staging service status
aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-staging-service \
  --region us-east-2 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
```

---

## ⚠️ IMPORTANT: Exam Environment is NOT Auto-Deployed

**The exam environment changes will NOT automatically deploy!**

Your exam environment (`pythonide-exam-task-service`) is:
- ✅ Already deployed and running
- ✅ Uses separate Docker image (`pythonide-exam:latest` in ECR)
- ❌ **NOT** managed by GitHub Actions CI/CD
- ✅ Must be manually updated if you change code

### When Does Exam Environment Need Manual Update?

**Only if you modify these files:**
- `server/*` - Backend Python code
- `src/*` - Frontend Vue.js code
- `Dockerfile` - Docker build configuration

**You DON'T need to update exam environment for:**
- Documentation changes ✅ (your current push)
- Scripts in `deployment/` ✅
- Configuration files ✅
- Database scripts ✅ (already run once)

---

## 🎯 Recommended Workflow

### Option 1: Push to Staging First (Recommended)

**What you should do now:**

```bash
# 1. Push to staging (safe)
git push origin staging

# 2. Wait for staging deployment to complete
# Check: https://github.com/YOUR_USERNAME/YOUR_REPO/actions

# 3. Test staging environment
# (Your staging service at its ALB endpoint)

# 4. If everything works, merge to main
git checkout main
git merge staging
git push origin main

# 5. This will deploy to production main IDE
# (Exam IDE is unaffected)
```

### Option 2: Push Directly to Main (Faster but riskier)

**Only if you're confident:**

```bash
# Switch to main branch
git checkout main

# Merge staging into main
git merge staging

# Push to main (triggers production deployment)
git push origin main

# ⚠️ This will deploy to pythonide-service (main IDE)
# ✅ Exam IDE is still unaffected
```

---

## 🔧 If You Need to Update Exam Environment Code

If you later modify backend/frontend code that exam environment should use:

```bash
# 1. Build exam Docker image
docker build --platform linux/amd64 \
  -t 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-exam:latest .

# 2. Push to exam ECR repository
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin \
  653306034507.dkr.ecr.us-east-2.amazonaws.com

docker push 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-exam:latest

# 3. Force redeploy exam service
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-exam-task-service \
  --force-new-deployment \
  --region us-east-2

# 4. Wait for deployment
aws ecs wait services-stable \
  --cluster pythonide-cluster \
  --services pythonide-exam-task-service \
  --region us-east-2
```

---

## 📊 Quick Reference

### Safe Actions:
```bash
✅ git push origin staging     # Deploys to staging only
✅ git push origin main         # Deploys to main IDE only
✅ Push documentation changes   # No service impact
✅ Merge staging → main         # Controlled production update
```

### Actions Requiring Care:
```bash
⚠️ Modifying server/ or src/    # Affects deployed services
⚠️ git push origin main         # Production deployment
⚠️ Changing Dockerfile          # Requires rebuild
```

### Exam Environment Update (Manual Only):
```bash
🔧 Build + push to pythonide-exam ECR
🔧 Force redeploy pythonide-exam-task-service
🔧 NOT triggered by GitHub Actions
```

---

## 🎉 Summary

**Current situation:**
- You're on `staging` branch
- Your changes are documentation + scripts + cleanup
- Exam environment is already deployed and working

**Recommended action:**
1. Push to staging: `git push origin staging` ✅ **SAFE**
2. Test staging deployment
3. Merge to main when ready
4. Exam environment continues working unchanged

**Key point:**
- Pushing to staging/main does NOT affect exam environment
- Exam environment is manually deployed and separate
- Your changes are safe to commit and push

---

**Ready to push?** Run the commands in Step 2-4 above! 🚀