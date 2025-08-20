#!/bin/bash

# Complete the Azure setup (Web App already created)
set -e

echo "═══════════════════════════════════════════════════════"
echo "   Completing Azure Setup for Python IDE"
echo "═══════════════════════════════════════════════════════"
echo ""

# Your already created resources
RESOURCE_GROUP="PythonIDE-RG"
APP_NAME="pythonide-3d84299d"

echo "✅ Using existing Web App: $APP_NAME"
echo ""

# Configure App Settings (using SQLite for now)
echo "⚙️ Configuring Application Settings..."

SECRET_KEY=$(openssl rand -base64 32)

az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        DATABASE_URL="sqlite:///pythonide.db" \
        IDE_SECRET_KEY="$SECRET_KEY" \
        MAX_CONCURRENT_EXECUTIONS=60 \
        EXECUTION_TIMEOUT=30 \
        MEMORY_LIMIT_MB=256 \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true \
        WEBSITES_PORT=8080 \
        WEBSITE_RUN_FROM_PACKAGE=0 \
    --output none

echo "✅ Settings configured"

# Enable WebSockets and Always On
echo "🔌 Enabling WebSockets and Always On..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --web-sockets-enabled true \
    --always-on true \
    --output none

# Set startup command
echo "🚀 Setting startup command..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "cd server && python server.py" \
    --output none

echo "✅ Web app configuration complete"

# Setup Git deployment
echo ""
echo "📤 Setting up Git Deployment..."

DEPLOYMENT_URL=$(az webapp deployment source config-local-git \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query url \
    --output tsv)

git remote remove azure 2>/dev/null || true
git remote add azure $DEPLOYMENT_URL

echo "✅ Git deployment configured"

# Save configuration
cat > azure-config.json << EOF
{
    "resourceGroup": "$RESOURCE_GROUP",
    "appName": "$APP_NAME",
    "location": "canadacentral",
    "appUrl": "https://$APP_NAME.azurewebsites.net",
    "deploymentUrl": "$DEPLOYMENT_URL"
}
EOF

# Create deployment script
cat > deploy.sh << 'EOF'
#!/bin/bash
echo "Building frontend..."
npm install && npm run build
echo "Deploying to Azure..."
git add .
git commit -m "Deploy to Azure" || true
git push azure main:master --force
echo "Deployment complete!"
echo "View app at: https://pythonide-3d84299d.azurewebsites.net"
EOF
chmod +x deploy.sh

# Create log viewer
cat > logs.sh << 'EOF'
#!/bin/bash
az webapp log tail --name pythonide-3d84299d --resource-group PythonIDE-RG
EOF
chmod +x logs.sh

# Create SSH script
cat > ssh.sh << 'EOF'
#!/bin/bash
az webapp ssh --name pythonide-3d84299d --resource-group PythonIDE-RG
EOF
chmod +x ssh.sh

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📌 Your Azure Resources:"
echo "  • App URL: https://pythonide-3d84299d.azurewebsites.net"
echo "  • Location: Canada Central (perfect for US users!)"
echo "  • Database: SQLite (can upgrade to PostgreSQL later)"
echo ""
echo "🚀 Deploy your app now:"
echo "  ./deploy.sh"
echo ""
echo "📊 Monitor logs:"
echo "  ./logs.sh"
echo ""
echo "🔧 SSH into container:"
echo "  ./ssh.sh"
echo ""
echo "💡 To add PostgreSQL later:"
echo "  1. Run: az provider register --namespace Microsoft.DBforPostgreSQL"
echo "  2. Wait 2 minutes"
echo "  3. Run: ./add-postgresql.sh"
echo ""