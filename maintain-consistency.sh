#!/bin/bash

# Maintain Consistency Between Local and Production
# This script helps you sync changes between local dev and production

set -e

echo "🔄 PythonIDE Environment Consistency Manager"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  sync-from-prod    Download latest from production EFS"
    echo "  sync-to-prod      Push local changes to production (via git)"
    echo "  backup-local      Create backup of local environment"
    echo "  check-diff        Compare local vs expected structure"
    echo "  fix-permissions   Fix file permissions and ownership"
    echo "  help              Show this help message"
    echo ""
}

backup_local() {
    echo "💾 Creating backup of local environment..."
    BACKUP_DIR="backups/backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [ -d "server/projects/ide" ]; then
        cp -r "server/projects/ide" "$BACKUP_DIR/"
        print_status "Local environment backed up to: $BACKUP_DIR/"
    else
        print_warning "No local IDE directory found to backup"
    fi
}

check_diff() {
    echo "🔍 Checking directory structure consistency..."
    
    LOCAL_BASE="server/projects/ide"
    
    if [ ! -d "$LOCAL_BASE" ]; then
        echo -e "${RED}✗${NC} Local IDE directory not found: $LOCAL_BASE"
        return 1
    fi
    
    echo ""
    echo "📊 Local Directory Structure:"
    echo "├── Local/ ($(ls -1 "$LOCAL_BASE/Local" 2>/dev/null | grep -v '^\.' | grep -v README | wc -l) directories)"
    
    if [ -d "$LOCAL_BASE/Local" ]; then
        # Count students vs admins
        student_count=0
        admin_count=0
        
        for dir in "$LOCAL_BASE/Local"/*; do
            if [ -d "$dir" ]; then
                dirname=$(basename "$dir")
                if [[ "$dirname" =~ ^(sl7927|sa9082|et2434)$ ]]; then
                    admin_count=$((admin_count + 1))
                elif [[ ! "$dirname" =~ ^\.|README|_migrated ]]; then
                    student_count=$((student_count + 1))
                fi
            fi
        done
        
        echo "│   ├── Students: $student_count"
        echo "│   └── Admins: $admin_count"
    fi
    
    echo "└── Lecture Notes/"
    if [ -d "$LOCAL_BASE/Lecture Notes" ]; then
        lecture_count=$(find "$LOCAL_BASE/Lecture Notes" -maxdepth 1 -type d | grep -v "^$LOCAL_BASE/Lecture Notes$" | wc -l)
        file_count=$(find "$LOCAL_BASE/Lecture Notes" -type f | wc -l)
        echo "    ├── Subdirectories: $lecture_count"
        echo "    └── Files: $file_count"
    fi
    
    echo ""
    print_status "Directory structure analysis complete"
}

sync_from_prod() {
    print_info "This would download latest data from production EFS"
    print_warning "Not implemented yet - requires ECS exec or EFS access point"
    echo ""
    echo "Alternative: Use the main sync script:"
    echo "./sync-local-with-production.sh"
}

sync_to_prod() {
    echo "🚀 Syncing local changes to production via CI/CD..."
    
    # Check if there are uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo ""
        echo "📝 Uncommitted changes detected:"
        git status --short
        echo ""
        
        read -p "Commit and push these changes? (y/n): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Add all changes
            git add .
            
            # Get commit message
            read -p "Enter commit message: " commit_msg
            if [ -z "$commit_msg" ]; then
                commit_msg="Update IDE directory structure and configurations"
            fi
            
            # Commit
            git commit -m "$commit_msg"
            
            # Push to trigger CI/CD
            current_branch=$(git branch --show-current)
            print_info "Pushing to branch: $current_branch"
            git push origin "$current_branch"
            
            print_status "Changes pushed! CI/CD will deploy to production automatically."
            print_info "Check GitHub Actions for deployment progress."
        else
            print_warning "Aborted sync to production"
        fi
    else
        print_info "No uncommitted changes detected"
        
        read -p "Push anyway to trigger deployment? (y/n): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            current_branch=$(git branch --show-current)
            git push origin "$current_branch"
            print_status "Pushed to trigger deployment!"
        fi
    fi
}

fix_permissions() {
    echo "🔧 Fixing file permissions and ownership..."
    
    LOCAL_BASE="server/projects/ide"
    
    if [ -d "$LOCAL_BASE" ]; then
        # Fix directory permissions
        find "$LOCAL_BASE" -type d -exec chmod 755 {} \;
        
        # Fix file permissions
        find "$LOCAL_BASE" -type f -name "*.py" -exec chmod 644 {} \;
        find "$LOCAL_BASE" -type f -name "*.config" -exec chmod 644 {} \;
        find "$LOCAL_BASE" -type f -name "README.md" -exec chmod 644 {} \;
        
        print_status "File permissions fixed"
    else
        print_warning "Local IDE directory not found"
    fi
}

# Main script logic
case "${1:-help}" in
    "sync-from-prod")
        sync_from_prod
        ;;
    "sync-to-prod")
        sync_to_prod
        ;;
    "backup-local")
        backup_local
        ;;
    "check-diff")
        check_diff
        ;;
    "fix-permissions")
        fix_permissions
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac