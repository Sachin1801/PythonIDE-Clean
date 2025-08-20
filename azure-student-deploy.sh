#!/bin/bash

# Azure Student Account Deployment Script for Python IDE
# This script sets up everything with your $100 free credits

set -e

echo "═══════════════════════════════════════════════════════"
echo "   Azure Student Deployment for Python IDE"
echo "   Using your $100 free credits efficiently"
echo "═══════════════════════════════════════════════════════"
echo ""

# Configuration
RESOURCE_GROUP="PythonIDE-Student-RG"
LOCATION="eastus"
APP_NAME="pythonide-$(openssl rand -hex 4)"
DB_NAME="pythonide-db-$(openssl rand -hex 4)"
PLAN_NAME="PythonIDE-Student-Plan"
DB_ADMIN="pythonideadmin"
DB_PASSWORD="PyIDE@$(openssl rand -base64 12)"

echo "🔧 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  App Name: $APP_NAME"
echo "  Database: $DB_NAME"
echo "  Location: $LOCATION"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Installing..."
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
fi

# Login to Azure
echo "📝 Step 1: Login to Azure"
echo "Please login with your Microsoft account linked to GitHub Student..."
az login

# Get subscription and set it
echo "📋 Setting subscription..."
SUBSCRIPTION=$(az account show --query id -o tsv)
echo "  Subscription ID: $SUBSCRIPTION"

# Create Resource Group
echo ""
echo "📦 Step 2: Creating Resource Group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output none
echo "✅ Resource group created"

# Create App Service Plan (B1 tier - included in free credits)
echo ""
echo "🏗️ Step 3: Creating App Service Plan..."
az appservice plan create \
    --name $PLAN_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B1 \
    --is-linux \
    --output none
echo "✅ App Service Plan created (B1 tier)"

# Create Web App
echo ""
echo "🌐 Step 4: Creating Web App..."
az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $PLAN_NAME \
    --runtime "PYTHON:3.11" \
    --output none
echo "✅ Web App created: https://$APP_NAME.azurewebsites.net"

# Create PostgreSQL Flexible Server (cheaper than Single Server)
echo ""
echo "🗄️ Step 5: Creating PostgreSQL Database..."
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

# Configure firewall for Azure services
echo "🔥 Configuring database firewall..."
az postgres flexible-server firewall-rule create \
    --name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --rule-name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 255.255.255.255 \
    --output none

# Create database
echo "📊 Creating database..."
az postgres flexible-server db create \
    --server-name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --database-name pythonide \
    --output none
echo "✅ PostgreSQL database created"

# Configure App Settings
echo ""
echo "⚙️ Step 6: Configuring Application Settings..."

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
        WEBSITE_WEBDEPLOY_USE_SCM=true \
    --output none

# Enable WebSockets
echo "🔌 Enabling WebSockets..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --web-sockets-enabled true \
    --output none

# Set startup command
echo "🚀 Setting startup command..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "cd server && python server.py" \
    --output none

echo "✅ Application configured"

# Setup deployment
echo ""
echo "📤 Step 7: Setting up Git Deployment..."

# Configure local git
DEPLOYMENT_URL=$(az webapp deployment source config-local-git \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query url \
    --output tsv)

# Add Azure remote
git remote remove azure 2>/dev/null || true
git remote add azure $DEPLOYMENT_URL

echo "✅ Git deployment configured"

# Create Application Insights (Free tier)
echo ""
echo "📊 Step 8: Setting up Monitoring..."
az monitor app-insights component create \
    --app "$APP_NAME-insights" \
    --location $LOCATION \
    --resource-group $RESOURCE_GROUP \
    --application-type web \
    --output none

INSTRUMENTATION_KEY=$(az monitor app-insights component show \
    --app "$APP_NAME-insights" \
    --resource-group $RESOURCE_GROUP \
    --query instrumentationKey \
    --output tsv)

az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY \
    --output none

echo "✅ Application Insights configured"

# Save configuration
echo ""
echo "💾 Saving configuration..."
cat > azure-config.json << EOF
{
    "resourceGroup": "$RESOURCE_GROUP",
    "appName": "$APP_NAME",
    "databaseName": "$DB_NAME",
    "databaseAdmin": "$DB_ADMIN",
    "databasePassword": "$DB_PASSWORD",
    "appUrl": "https://$APP_NAME.azurewebsites.net",
    "kuduUrl": "https://$APP_NAME.scm.azurewebsites.net",
    "deploymentUrl": "$DEPLOYMENT_URL"
}
EOF

echo "✅ Configuration saved to azure-config.json"

# Create deployment helper scripts
cat > deploy-to-azure.sh << 'EOF'
#!/bin/bash
echo "Deploying to Azure..."
git push azure main:master --force
echo "Deployment complete!"
echo "View logs: az webapp log tail --name $(jq -r .appName azure-config.json) --resource-group $(jq -r .resourceGroup azure-config.json)"
EOF
chmod +x deploy-to-azure.sh

cat > azure-logs.sh << 'EOF'
#!/bin/bash
CONFIG=$(cat azure-config.json)
APP_NAME=$(echo $CONFIG | jq -r .appName)
RG=$(echo $CONFIG | jq -r .resourceGroup)
az webapp log tail --name $APP_NAME --resource-group $RG
EOF
chmod +x azure-logs.sh

# Summary
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT SETUP COMPLETE!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📌 Your Azure Resources:"
echo "  • App URL: https://$APP_NAME.azurewebsites.net"
echo "  • Kudu Console: https://$APP_NAME.scm.azurewebsites.net"
echo "  • Database: $DB_NAME.postgres.database.azure.com"
echo ""
echo "💰 Estimated Monthly Cost (covered by credits):"
echo "  • App Service (B1): ~$13/month"
echo "  • PostgreSQL (Burstable B1ms): ~$12/month"
echo "  • Application Insights: Free (5GB/month)"
echo "  • Total: ~$25/month (4 months with $100 credits)"
echo ""
echo "🚀 Next Steps:"
echo "  1. Deploy your code:"
echo "     ./deploy-to-azure.sh"
echo ""
echo "  2. View logs:"
echo "     ./azure-logs.sh"
echo ""
echo "  3. Open your app:"
echo "     https://$APP_NAME.azurewebsites.net"
echo ""
echo "📝 Credentials saved in azure-config.json"
echo "⚠️  Keep this file secure - it contains passwords!"
echo ""