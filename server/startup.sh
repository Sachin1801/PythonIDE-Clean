#!/bin/bash
set -e

echo "Starting Python IDE Server..."
echo "=========================="

# Function to handle shutdown
shutdown() {
    echo "Received shutdown signal, cleaning up..."
    kill -TERM "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
    echo "Server stopped gracefully"
    exit 0
}

# Trap signals for graceful shutdown
trap shutdown SIGTERM SIGINT

# Check if database is accessible
echo "Checking database connection..."
python -c "
import os
import sys
import psycopg2
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('WARNING: No DATABASE_URL found, using local database')
    sys.exit(0)

try:
    url = urlparse(db_url)
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port or 5432,
        database=url.path[1:],
        user=url.username,
        password=url.password,
        connect_timeout=10
    )
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    print('Server will attempt to reconnect...')
"

# Run migrations
echo "Running database migrations..."
python server/migrations/add_modified_at_column.py || {
    echo "Migration failed, but continuing..."
}

# Start the server with automatic restart on failure
while true; do
    echo "Starting server on port ${PORT:-8080}..."
    python server/server.py &
    SERVER_PID=$!
    
    # Wait for server process
    wait "$SERVER_PID"
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Server exited normally"
        break
    else
        echo "Server crashed with exit code $EXIT_CODE, restarting in 5 seconds..."
        sleep 5
    fi
done