#!/bin/bash

echo "🚀 Deploying Python IDE to Railway"
echo "=================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed"
    echo "Install it with: npm install -g @railway/cli"
    echo "Or visit: https://docs.railway.app/develop/cli"
    exit 1
fi

# Login to Railway
echo "📝 Logging into Railway..."
railway login

# Initialize Railway project (if not already)
if [ ! -f ".railway/config.json" ]; then
    echo "🎯 Initializing Railway project..."
    railway init
fi

# Link to existing project or create new
echo "🔗 Linking Railway project..."
railway link

# Note about PostgreSQL database
echo "📌 Note: Add PostgreSQL database manually in Railway dashboard"
echo "   Go to: https://railway.app/project/4de99089-ea56-47b4-8ef2-21121839a0ca"
echo "   Click 'New' → 'Database' → 'Add PostgreSQL'"

# Deploy the application
echo "🚀 Deploying application..."
railway up

# Show deployment URL
echo "✅ Deployment complete!"
echo "🌐 Getting deployment URL..."
railway open

echo ""
echo "📋 Next steps:"
echo "1. Go to Railway dashboard"
echo "2. Set environment variables:"
echo "   - IDE_SECRET_KEY (generate a secure key)"
echo "   - MAX_CONCURRENT_EXECUTIONS=60"
echo "   - EXECUTION_TIMEOUT=30"
echo "   - MEMORY_LIMIT_MB=128"
echo "3. The PostgreSQL DATABASE_URL is automatically configured"
echo "4. Monitor logs with: railway logs"