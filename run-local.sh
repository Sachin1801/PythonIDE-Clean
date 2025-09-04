#!/bin/bash

# Simple local development script for PythonIDE
set -e

echo "=========================================="
echo "🚀 STARTING PYTHONIDE LOCAL DEVELOPMENT"
echo "=========================================="

# Set environment variables for local development
export IDE_DATA_PATH="/tmp/pythonide-data"
export DATABASE_URL="postgresql://pythonide:password@localhost:5432/pythonide"
export IDE_SECRET_KEY="local-dev-key-change-in-production"
export PORT=8080

echo "✅ Environment configured:"
echo "   - Data Path: $IDE_DATA_PATH"
echo "   - Database: Local PostgreSQL"
echo "   - Port: $PORT"

# Check if local PostgreSQL is running
if ! pg_isready -d "$DATABASE_URL" 2>/dev/null; then
    echo ""
    echo "⚠️  Local PostgreSQL not detected. Please ensure:"
    echo "   1. PostgreSQL is installed and running"
    echo "   2. Database 'pythonide' exists"
    echo "   3. User 'pythonide' has access"
    echo ""
    echo "Quick setup:"
    echo "   sudo -u postgres createdb pythonide"
    echo "   sudo -u postgres psql -c \"CREATE USER pythonide WITH PASSWORD 'password';\""
    echo "   sudo -u postgres psql -c \"GRANT ALL ON DATABASE pythonide TO pythonide;\""
    echo ""
fi

# Ensure student directories exist locally
echo ""
echo "📁 Ensuring student directories exist locally..."
python3 -c "
import sys, os
sys.path.append('server')
from common.file_storage import file_storage
print(f'✅ Storage initialized at: {file_storage.storage_root}')
print(f'✅ IDE base: {file_storage.ide_base}')
if os.path.exists(os.path.join(file_storage.ide_base, 'Local')):
    student_count = len(os.listdir(os.path.join(file_storage.ide_base, 'Local')))
    print(f'✅ Found {student_count} student directories')
else:
    print('⚠️  No student directories found')
"

echo ""
echo "🎯 Starting development server..."
echo "   - Frontend: Build with 'npm run build' first"
echo "   - Backend: Will serve on http://localhost:8080"
echo ""

# Navigate to server directory and start
cd server
python3 server.py --port $PORT