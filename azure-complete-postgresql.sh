#!/bin/bash

# Complete PostgreSQL setup for already created Web App
set -e

echo "═══════════════════════════════════════════════════════"
echo "   Completing PostgreSQL Setup for Python IDE"
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

# Check if PostgreSQL provider is registered
echo "Checking PostgreSQL provider registration..."
REG_STATE=$(az provider show --namespace Microsoft.DBforPostgreSQL --query registrationState -o tsv)
if [ "$REG_STATE" != "Registered" ]; then
    echo "❌ PostgreSQL provider not registered yet."
    echo "   Run: az provider register --namespace Microsoft.DBforPostgreSQL"
    echo "   Then wait 2 minutes and run this script again."
    exit 1
fi
echo "✅ PostgreSQL provider is registered"
echo ""

# Create PostgreSQL Database
echo "🗄️ Creating PostgreSQL Database..."
echo "   This will take 5-10 minutes..."

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
    --yes \
    --output none

echo "✅ PostgreSQL server created"

# Configure firewall
echo "🔥 Configuring database firewall..."
az postgres flexible-server firewall-rule create \
    --name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --rule-name AllowAllAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 255.255.255.255 \
    --output none

# Create database
echo "📊 Creating pythonide database..."
az postgres flexible-server db create \
    --server-name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --database-name pythonide \
    --output none

echo "✅ Database setup complete"

# Configure App Settings with PostgreSQL
echo ""
echo "⚙️ Configuring Application Settings..."

DATABASE_URL="postgresql://$DB_ADMIN:$DB_PASSWORD@$DB_NAME.postgres.database.azure.com:5432/pythonide?sslmode=require"
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
    --output none

echo "✅ Application settings configured"

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
    "databaseName": "$DB_NAME",
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
echo "Deployment complete!"
echo "View app at: https://pythonide-3d84299d.azurewebsites.net"
EOF
chmod +x deploy.sh

cat > logs.sh << 'EOF'
#!/bin/bash
az webapp log tail --name pythonide-3d84299d --resource-group PythonIDE-RG
EOF
chmod +x logs.sh

cat > ssh.sh << 'EOF'
#!/bin/bash
az webapp ssh --name pythonide-3d84299d --resource-group PythonIDE-RG
EOF
chmod +x ssh.sh

# Summary
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ POSTGRESQL DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📌 Your Azure Resources:"
echo "  • App URL: https://pythonide-3d84299d.azurewebsites.net"
echo "  • Database: $DB_NAME.postgres.database.azure.com"
echo "  • Location: Canada Central (excellent for US users!)"
echo ""
echo "🔐 Database Credentials (saved in azure-config.json):"
echo "  • Admin: $DB_ADMIN"
echo "  • Password: [hidden - see azure-config.json]"
echo ""
echo "💰 Monthly Cost (covered by your $100 credits):"
echo "  • App Service (B1): ~$13/month"
echo "  • PostgreSQL (Burstable): ~$12/month"
echo "  • Total: ~$25/month (4 months with credits)"
echo ""
echo "🚀 Deploy your code now:"
echo "  ./deploy.sh"
echo ""
echo "📊 Monitor logs:"
echo "  ./logs.sh"
echo ""
echo "✅ Everything is ready with PostgreSQL!"