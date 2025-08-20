#!/bin/bash

# Azure Student Account Deployment Script for Python IDE
# Fixed version with region detection

set -e

echo "═══════════════════════════════════════════════════════"
echo "   Azure Student Deployment for Python IDE"
echo "   Using your $100 free credits efficiently"
echo "═══════════════════════════════════════════════════════"
echo ""

# First, detect allowed regions for your subscription
echo "🔍 Detecting allowed regions for your Azure Student subscription..."
ALLOWED_REGIONS=$(az account list-locations --query "[?metadata.regionCategory=='Recommended'].name" -o tsv 2>/dev/null | head -5)

if [ -z "$ALLOWED_REGIONS" ]; then
    # Fallback to common student-allowed regions
    echo "Using common Azure Student regions..."
    REGIONS=("centralus" "westus2" "southcentralus" "northcentralus" "westus")
else
    REGIONS=($ALLOWED_REGIONS)
fi

echo "Available regions:"
for i in "${!REGIONS[@]}"; do
    echo "  $((i+1)). ${REGIONS[$i]}"
done
echo ""
read -p "Select a region (1-${#REGIONS[@]}): " REGION_CHOICE
LOCATION=${REGIONS[$((REGION_CHOICE-1))]}

# Configuration
RESOURCE_GROUP="PythonIDE-Student-RG"
APP_NAME="pythonide-$(openssl rand -hex 4)"
DB_NAME="pythonide-db-$(openssl rand -hex 4)"
PLAN_NAME="PythonIDE-Student-Plan"
DB_ADMIN="pythonideadmin"
DB_PASSWORD="PyIDE@$(openssl rand -base64 12)"

echo ""
echo "🔧 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  App Name: $APP_NAME"
echo "  Database: $DB_NAME"
echo "  Location: $LOCATION"
echo ""

# Check if already logged in
if ! az account show &>/dev/null; then
    echo "📝 Step 1: Login to Azure"
    echo "Please login with your Microsoft account linked to GitHub Student..."
    az login --use-device-code
else
    echo "✅ Already logged in to Azure"
fi

# Get subscription and set it
echo "📋 Setting subscription..."
SUBSCRIPTION=$(az account show --query id -o tsv)
echo "  Subscription ID: $SUBSCRIPTION"

# Clean up existing resource group if it exists
echo ""
echo "🧹 Cleaning up any existing resources..."
az group delete --name $RESOURCE_GROUP --yes --no-wait 2>/dev/null || true
sleep 5

# Create Resource Group
echo ""
echo "📦 Step 2: Creating Resource Group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output none
echo "✅ Resource group created in $LOCATION"

# Create App Service Plan (Free F1 tier first, then upgrade if needed)
echo ""
echo "🏗️ Step 3: Creating App Service Plan..."
echo "  Trying Free tier (F1) first..."
if ! az appservice plan create \
    --name $PLAN_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku F1 \
    --is-linux \
    --output none 2>/dev/null; then
    
    echo "  Free tier not available, using Basic B1..."
    az appservice plan create \
        --name $PLAN_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku B1 \
        --is-linux \
        --output none
fi
echo "✅ App Service Plan created"

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

# For students, we'll use a simpler database solution
echo ""
echo "🗄️ Step 5: Setting up Database..."
echo "  Note: Using SQLite for initial deployment (free)"
echo "  You can upgrade to PostgreSQL later if needed"

# Configure App Settings for SQLite first
echo ""
echo "⚙️ Step 6: Configuring Application Settings..."

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

# Configure deployment credentials
DEPLOY_USER="pythonide$(openssl rand -hex 4)"
DEPLOY_PASS="Deploy@$(openssl rand -base64 12)"

az webapp deployment user set \
    --user-name $DEPLOY_USER \
    --password "$DEPLOY_PASS" \
    --output none

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

# Try to create Application Insights (may not be available in all regions)
echo ""
echo "📊 Step 8: Setting up Monitoring (if available)..."
if az monitor app-insights component create \
    --app "$APP_NAME-insights" \
    --location $LOCATION \
    --resource-group $RESOURCE_GROUP \
    --application-type web \
    --output none 2>/dev/null; then
    
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
else
    echo "⚠️  Application Insights not available in this region (not critical)"
fi

# Save configuration
echo ""
echo "💾 Saving configuration..."
cat > azure-config.json << EOF
{
    "resourceGroup": "$RESOURCE_GROUP",
    "appName": "$APP_NAME",
    "location": "$LOCATION",
    "appUrl": "https://$APP_NAME.azurewebsites.net",
    "kuduUrl": "https://$APP_NAME.scm.azurewebsites.net",
    "deploymentUrl": "$DEPLOYMENT_URL",
    "deployUser": "$DEPLOY_USER",
    "deployPassword": "$DEPLOY_PASS"
}
EOF

echo "✅ Configuration saved to azure-config.json"

# Create deployment helper scripts
cat > deploy-to-azure.sh << 'EOF'
#!/bin/bash
echo "Building frontend..."
npm install && npm run build
echo "Deploying to Azure..."
git add .
git commit -m "Deploy to Azure" || true
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
echo "  • Region: $LOCATION"
echo ""
echo "💰 Cost with Student Credits:"
echo "  • App Service: Free (F1) or ~$13/month (B1)"
echo "  • Database: Using SQLite (free)"
echo "  • Total: $0-13/month"
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
echo "📝 Deployment credentials saved in azure-config.json"
echo ""
echo "🔄 To upgrade to PostgreSQL later:"
echo "   Run: ./upgrade-to-postgresql.sh"
echo ""

# Create PostgreSQL upgrade script
cat > upgrade-to-postgresql.sh << EOF
#!/bin/bash
echo "Upgrading to PostgreSQL..."
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
    --yes

az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings DATABASE_URL="postgresql://$DB_ADMIN:$DB_PASSWORD@$DB_NAME.postgres.database.azure.com:5432/pythonide?sslmode=require"

echo "PostgreSQL upgrade complete!"
EOF
chmod +x upgrade-to-postgresql.sh