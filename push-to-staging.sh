#!/bin/bash
# Safe Push Script - Exam Environment Changes to Staging

echo "🚀 Safe Push to Staging Branch"
echo "================================"
echo ""

# Verify we're on staging branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "staging" ]; then
    echo "⚠️  WARNING: You're on branch '$CURRENT_BRANCH', not 'staging'"
    echo "Switch to staging first: git checkout staging"
    exit 1
fi

echo "✅ Current branch: $CURRENT_BRANCH"
echo ""

# Show what will be committed
echo "📋 Files to be committed:"
echo "========================="
git status --short
echo ""

read -p "Continue with commit? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 0
fi

echo ""
echo "📦 Adding files..."

# Add new exam environment files
git add server/init_exam_users.py
git add server/handlers/lockdown_handler.py
git add docker-compose.exam.yml
git add deployment/ecs-task-definition-exam-fixed.json
git add deployment/setup-exam-database.sql
git add deployment/EXAM_ENVIRONMENT_WORKING.md
git add deployment/ROUTING_CONFIGURATION.md
git add deployment/CLOUDFRONT_STATUS.md

# Add comprehensive documentation
git add docs/EXAM_ENVIRONMENT_GUIDE.md
git add ROOT_CLEANUP_GUIDE.md
git add SAFE_PUSH_GUIDE.md
git add deployment/FILES_TO_DELETE.md

# Add CloudFront config
git add cloudfront-config.json

# Add modified files
git add .gitignore
git add server/command/hybrid_repl_thread.py

# Add all deletions (cleanup files)
git add -u

echo "✅ Files staged for commit"
echo ""

# Create commit
echo "📝 Creating commit..."
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

Infrastructure:
- Service: pythonide-exam-task-service
- Target Group: pythonide-exam-tg
- Database: pythonide_exam
- Access URL: http://exam.pythonide-classroom.tech/

Documentation:
- Comprehensive guide in docs/EXAM_ENVIRONMENT_GUIDE.md
- Covers network capacity, lockdown mode, exam procedures
- Troubleshooting and emergency procedures included

Deployment: Manual deployment to pythonide-exam-task-service (not auto-deployed)

🤖 Generated with Claude Code
https://claude.com/claude-code

Co-Authored-By: Claude <noreply@anthropic.com>"

if [ $? -eq 0 ]; then
    echo "✅ Commit created successfully"
else
    echo "❌ Commit failed"
    exit 1
fi

echo ""
read -p "Push to origin/staging? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Push cancelled"
    echo "💡 You can push manually later with: git push origin staging"
    exit 0
fi

echo ""
echo "🚀 Pushing to origin/staging..."
git push origin staging

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to staging!"
    echo ""
    echo "📊 What happens next:"
    echo "  1. GitHub Actions will deploy to pythonide-staging-service"
    echo "  2. Main production IDE (pythonide-service) is UNAFFECTED"
    echo "  3. Exam IDE (pythonide-exam-task-service) is UNAFFECTED"
    echo ""
    echo "🔗 Monitor deployment:"
    echo "  https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
    echo ""
    echo "✅ SAFE: This deployment does not affect production!"
else
    echo "❌ Push failed"
    exit 1
fi
