#!/bin/bash

# Deploy sz3991 (Shiwen Zhu) to AWS Production
# Run this script on AWS environment after pushing local changes

set -e  # Exit on any error

echo "=========================================="
echo "DEPLOYING SZ3991 TO AWS PRODUCTION"
echo "=========================================="
echo "Student: Shiwen Zhu (sz3991)"
echo "Password: EaS08VX%fcp8"
echo ""

# Check if we're in the right directory
if [[ ! -f "add_sz3991_to_aws_rds.py" ]]; then
    echo "❌ Error: Must run from PythonIDE-Clean root directory"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "server/venv" ]]; then
    echo "❌ Error: server/venv not found. Run from project root with venv set up."
    exit 1
fi

echo "📋 Step 1: Verifying current environment..."
python3 verify_sz3991_account.py || echo "⚠️  Pre-verification showed some issues (expected if user doesn't exist yet)"

echo ""
echo "📋 Step 2: Adding user to AWS RDS database..."
cd server
source venv/bin/activate
cd ..
python3 add_sz3991_to_aws_rds.py

echo ""
echo "📋 Step 3: Creating user directory on AWS EFS..."
python3 create_sz3991_efs_directory.py

echo ""
echo "📋 Step 4: Final verification..."
python3 verify_sz3991_account.py

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "🔑 LOGIN CREDENTIALS for sz3991:"
echo "Username: sz3991"
echo "Password: EaS08VX%fcp8"
echo "Full Name: Shiwen Zhu"
echo "Role: student"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Test login at the IDE interface"
echo "2. Verify file operations work"
echo "3. Test Python script execution"
echo "4. Check that user can only see their own directory"
echo ""
echo "🔗 Access URL: https://your-aws-load-balancer-url"