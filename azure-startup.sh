#!/bin/bash
# Azure App Service startup script

echo "Starting Python IDE on Azure App Service..."

# Azure provides these environment variables
echo "WEBSITE_HOSTNAME: $WEBSITE_HOSTNAME"
echo "WEBSITE_INSTANCE_ID: $WEBSITE_INSTANCE_ID"

# Run database migrations
echo "Running database migrations..."
python server/migrations/add_modified_at_column.py || true

# Create user directories
mkdir -p server/projects/ide/Local
mkdir -p "server/projects/ide/Lecture Notes"
mkdir -p server/projects/ide/Assignments
mkdir -p server/projects/ide/Tests

# Start the application
echo "Starting server on port ${WEBSITES_PORT:-8080}..."
cd server && python server.py --port ${WEBSITES_PORT:-8080}