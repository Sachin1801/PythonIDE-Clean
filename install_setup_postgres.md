# PostgreSQL Setup for Local Development

## Quick Setup (Ubuntu/WSL)

### 1. Install PostgreSQL
```bash
# Update packages
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start PostgreSQL service
sudo service postgresql start
```

### 2. Setup Database
```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt, run:
CREATE DATABASE pythonide;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE pythonide TO postgres;
\q
```

### 3. Verify Connection
```bash
# Test connection
psql -U postgres -d pythonide -h localhost -W
# Enter password: postgres
# You should see: pythonide=#
# Type \q to exit
```

### 4. Initialize Database Tables
```bash
cd server
python3 -c "from common.database import db_manager; print('Database initialized!')"
```

### 5. Create Test Users
```bash
python3 setup_users.py
```

## Alternative: Use Docker (Easiest)

If you have Docker installed:

```bash
# Run PostgreSQL in Docker
docker run --name pythonide-postgres \
  -e POSTGRES_DB=pythonide \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d postgres:14

# Database will be available at:
# postgresql://postgres:postgres@localhost:5432/pythonide
```

## Running the Application

Once PostgreSQL is set up:

```bash
# Start the application
./run_local.sh

# Or manually:
# Terminal 1 - Backend
cd server
python server.py --port 10086

# Terminal 2 - Frontend
npm run serve
```

## Troubleshooting

### Error: "Connection refused"
- PostgreSQL not running: `sudo service postgresql start`
- Wrong password: Check `.env` file matches your PostgreSQL setup

### Error: "Database pythonide does not exist"
```bash
sudo -u postgres createdb pythonide
```

### Error: "Role postgres does not exist"
```bash
sudo -u postgres createuser postgres -s
```

### Reset Everything
```bash
# Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS pythonide;"
sudo -u postgres psql -c "CREATE DATABASE pythonide;"

# Reinitialize
cd server
python setup_users.py
```

## Environment Variables

Make sure `server/.env` has:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pythonide
```

## Test Accounts

After running `setup_users.py`:
- Professor: `professor` / `ChangeMeASAP2024!`
- Student: `sa9082` / `sa90822024`