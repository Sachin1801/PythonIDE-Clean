#!/bin/bash

# Complete PostgreSQL setup with proper waiting
set -e

echo "═══════════════════════════════════════════════════════"
echo "   Setting up PostgreSQL for Python IDE"
echo "═══════════════════════════════════════════════════════"
echo ""

# Your existing resources
RESOURCE_GROUP="PythonIDE-RG"
APP_NAME="pythonide-3d84299d"
LOCATION="canadacentral"

# Database configuration
DB_NAME="pythonide-db-$(openssl rand -hex 4)"
DB_ADMIN="pythonideadmin"
DB_PASSWORD="PyIDE@$(openssl rand -base64 12)"

echo "✅ Using existing Web App: $APP_NAME"
echo ""

# Create PostgreSQL Database with simpler approach
echo "🗄️ Creating PostgreSQL Database..."
echo "   Database name: $DB_NAME"
echo "   This will take 5-10 minutes..."
echo ""

# Create the PostgreSQL server without auto-firewall rules
az postgres flexible-server create \
    --name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --admin-user $DB_ADMIN \
    --admin-password "$DB_PASSWORD" \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --storage-size 32 \
    --version 15 \
    --public-access 0.0.0.0 \
    --yes

echo ""
echo "✅ PostgreSQL server created successfully!"

# Wait a bit for the server to be fully ready
echo "⏳ Waiting for server to be fully ready..."
sleep 10

# Now configure firewall rules
echo "🔥 Configuring firewall rules..."

# Allow Azure services
az postgres flexible-server firewall-rule create \
    --name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --rule-name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0 \
    --output none

# Allow all IPs (for development - restrict this in production)
az postgres flexible-server firewall-rule create \
    --name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --rule-name AllowAll \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 255.255.255.255 \
    --output none

echo "✅ Firewall rules configured"

# Create the database
echo "📊 Creating pythonide database..."
az postgres flexible-server db create \
    --server-name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --database-name pythonide \
    --output none

echo "✅ Database created"

# Get the full server hostname
DB_HOST=$(az postgres flexible-server show \
    --name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --query fullyQualifiedDomainName \
    --output tsv)

# Configure App Settings with PostgreSQL
echo ""
echo "⚙️ Configuring Application Settings..."

DATABASE_URL="postgresql://$DB_ADMIN:$DB_PASSWORD@$DB_HOST:5432/pythonide?sslmode=require"
SECRET_KEY=$(openssl rand -base64 32)

az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        DATABASE_URL="$DATABASE_URL" \
        IDE_SECRET_KEY="$SECRET_KEY" \
        MAX_CONCURRENT_EXECUTIONS=60 \
        EXECUTION_TIMEOUT=30 \
        MEMORY_LIMIT_MB=256 \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true \
        WEBSITES_PORT=8080 \
        WEBSITE_RUN_FROM_PACKAGE=0 \
    --output none

echo "✅ Application settings configured"

# Enable WebSockets and Always On
echo "🔌 Configuring web app features..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --web-sockets-enabled true \
    --always-on true \
    --output none

# Set startup command
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "cd server && python server.py" \
    --output none

echo "✅ Web app configuration complete"

# Setup Git deployment
echo ""
echo "📤 Setting up Git Deployment..."

# Get the deployment credentials
DEPLOY_USER=$(az webapp deployment list-publishing-credentials \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query publishingUserName \
    --output tsv)

# Configure local git
DEPLOYMENT_URL=$(az webapp deployment source config-local-git \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query url \
    --output tsv)

git remote remove azure 2>/dev/null || true
git remote add azure $DEPLOYMENT_URL

echo "✅ Git deployment configured"

# Save configuration
echo ""
echo "💾 Saving configuration..."
cat > azure-config.json << EOF
{
    "resourceGroup": "$RESOURCE_GROUP",
    "appName": "$APP_NAME",
    "databaseName": "$DB_NAME",
    "databaseHost": "$DB_HOST",
    "databaseAdmin": "$DB_ADMIN",
    "databasePassword": "$DB_PASSWORD",
    "location": "$LOCATION",
    "appUrl": "https://$APP_NAME.azurewebsites.net",
    "deploymentUrl": "$DEPLOYMENT_URL"
}
EOF

# Create helper scripts
cat > deploy.sh << 'EOF'
#!/bin/bash
echo "Building frontend..."
npm install && npm run build
echo "Deploying to Azure..."
git add .
git commit -m "Deploy to Azure" || true
git push azure main:master --force
echo ""
echo "Deployment initiated!"
echo "View deployment progress at: https://pythonide-3d84299d.scm.azurewebsites.net/DeploymentCenter"
echo "View app at: https://pythonide-3d84299d.azurewebsites.net"
EOF
chmod +x deploy.sh

cat > logs.sh << 'EOF'
#!/bin/bash
echo "Streaming logs from Azure..."
az webapp log tail --name pythonide-3d84299d --resource-group PythonIDE-RG
EOF
chmod +x logs.sh

cat > ssh.sh << 'EOF'
#!/bin/bash
echo "Opening SSH connection to Azure container..."
az webapp ssh --name pythonide-3d84299d --resource-group PythonIDE-RG
EOF
chmod +x ssh.sh

cat > restart.sh << 'EOF'
#!/bin/bash
echo "Restarting web app..."
az webapp restart --name pythonide-3d84299d --resource-group PythonIDE-RG
echo "Web app restarted!"
EOF
chmod +x restart.sh

# Summary
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ POSTGRESQL SETUP COMPLETE!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📌 Your Azure Resources:"
echo "  • App URL: https://$APP_NAME.azurewebsites.net"
echo "  • Database: $DB_HOST"
echo "  • Location: Canada Central"
echo ""
echo "🔐 Database Connection:"
echo "  • Host: $DB_HOST"
echo "  • Database: pythonide"
echo "  • Username: $DB_ADMIN"
echo "  • Password: Saved in azure-config.json"
echo ""
echo "💰 Cost (covered by your $100 credits):"
echo "  • ~$25/month total"
echo "  • 4 months free with your credits"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "  1. Deploy your code:"
echo "     ./deploy.sh"
echo ""
echo "  2. Monitor logs:"
echo "     ./logs.sh"
echo ""
echo "  3. If needed, restart app:"
echo "     ./restart.sh"
echo ""
echo "  4. SSH into container:"
echo "     ./ssh.sh"
echo ""
echo "✅ PostgreSQL is ready and connected to your app!"
echo "📝 All credentials saved in azure-config.json"