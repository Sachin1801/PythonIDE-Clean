# PythonIDE Deployment Guide

## Railway Deployment (Production)

### Prerequisites
- Railway CLI installed: `npm install -g @railway/cli`
- Railway account and project created

### Step 1: Deploy to Railway
```bash
# Login to Railway
railway login

# Link to your Railway project
railway link

# Deploy the application
railway up
```

### Step 2: Railway will automatically:
- Provision PostgreSQL database
- Set DATABASE_URL environment variable
- Build and deploy your application

### Step 3: Initialize Database

#### Option A: Use the Setup Endpoint (Recommended)
After deployment, visit your app URL and go to:
```
https://your-app.railway.app/api/setup
```
This will:
- Create default users (professor and sa9082)
- Set up directory structure
- Return login credentials

#### Option B: Use Railway Shell (if available)
```bash
# Connect to Railway shell
railway shell

# Then run inside the shell:
cd server
python migrations/create_users.py
```

### Step 4: Verify Deployment
```bash
# Check logs
railway logs

# Open your app
railway open
```

## Local Development Setup

### Option 1: Docker PostgreSQL (Recommended)
```bash
# Start PostgreSQL in Docker
docker run -d \
  --name pythonide-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=pythonide \
  -p 5432:5432 \
  postgres:15

# Install Python dependencies
cd server
pip install -r requirements.txt

# Run migrations
python migrations/create_users.py
python migrations/setup_directories.py

# Start the server
python server.py
```

### Option 2: Local PostgreSQL Installation
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql

# Create database
sudo -u postgres psql -c "CREATE DATABASE pythonide;"
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"

# Continue with Python setup as above
```

## Environment Variables

### Production (Railway)
Railway automatically sets:
- `DATABASE_URL`: PostgreSQL connection string
- `PORT`: Application port

### Local Development
Create `server/.env`:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pythonide
IDE_SECRET_KEY=local-dev-secret-key
MAX_CONCURRENT_EXECUTIONS=60
EXECUTION_TIMEOUT=30
MEMORY_LIMIT_MB=128
LOG_LEVEL=INFO
```

## Default Users

After running `migrations/create_users.py`:

**Professor Account:**
- Username: `professor`
- Password: `ChangeMeASAP2024!`

**Student Account:**
- Username: `sa9082`
- Password: `sa90822024`

## Directory Structure

The application creates this structure:
```
/server/projects/ide/
├── Local/
│   ├── sa9082/         # Student workspace
│   ├── professor/      # Professor workspace
│   └── ...
├── Lecture Notes/      # Professor uploads
├── Assignments/        # Assignment materials
└── Tests/             # Test materials
```

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database connection
railway run python -c "from common.database import db_manager; print('Connected!')"

# View logs
railway logs --tail 100
```

### Reset Database
```bash
# On Railway
railway run python -c "from common.database import db_manager; db_manager.reset_tables()"

# Locally
python -c "from common.database import db_manager; db_manager.reset_tables()"
```

## Security Notes

1. **Change default passwords immediately** after first login
2. Railway provides automatic SSL for database connections
3. All user passwords are bcrypt hashed
4. File access is restricted by user role and ownership

## Support

For issues or questions:
- Check Railway logs: `railway logs`
- Database status: `railway run python -c "from common.database import db_manager; print(db_manager.get_status())"`
- Contact: Sachin Adlakha