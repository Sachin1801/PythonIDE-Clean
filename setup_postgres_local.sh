#!/bin/bash

echo "🐘 Setting up PostgreSQL for local development..."
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed!"
    echo ""
    echo "Please install PostgreSQL first:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  Mac: brew install postgresql"
    echo "  Windows: Download from https://www.postgresql.org/download/windows/"
    exit 1
fi

echo "✅ PostgreSQL is installed"

# Start PostgreSQL service
echo "Starting PostgreSQL service..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo service postgresql start
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start postgresql
fi

# Create database and user
echo ""
echo "Creating database and user..."

# Create the database and user as postgres user
sudo -u postgres psql << EOF
-- Create user if not exists
DO
\$\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user
      WHERE usename = 'pythonide_user') THEN

      CREATE USER pythonide_user WITH PASSWORD 'pythonide_local_2024';
   END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE pythonide'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pythonide');
\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pythonide TO pythonide_user;

-- Connect to pythonide database
\c pythonide

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO pythonide_user;
EOF

echo ""
echo "✅ PostgreSQL setup complete!"
echo ""
echo "Database details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: pythonide"
echo "  User: pythonide_user"
echo "  Password: pythonide_local_2024"
echo ""
echo "Connection string:"
echo "  postgresql://pythonide_user:pythonide_local_2024@localhost:5432/pythonide"
echo ""
echo "Add this to your server/.env file:"
echo "  DATABASE_URL=postgresql://pythonide_user:pythonide_local_2024@localhost:5432/pythonide"