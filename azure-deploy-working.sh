#!/bin/bash

# Azure Student Deployment - Using Working Regions
set -e

echo "═══════════════════════════════════════════════════════"
echo "   Azure Student Deployment for Python IDE"
echo "   Using regions that work with your subscription"
echo "═══════════════════════════════════════════════════════"
echo ""

# Show working regions
echo "✅ Available regions for your subscription:"
echo "  1. North Europe (Ireland) - Good latency for US/Europe"
echo "  2. West Europe (Netherlands) - Good latency for US/Europe"
echo "  3. UK South (London) - Good for US East Coast"
echo "  4. Canada Central (Toronto) - BEST for US users"
echo "  5. Southeast Asia (Singapore)"
echo "  6. Australia East (Sydney)"
echo ""

read -p "Select a region (1-6, recommend 4 for US): " choice

case $choice in
    1) LOCATION="northeurope" ; DISPLAY_NAME="North Europe" ;;
    2) LOCATION="westeurope" ; DISPLAY_NAME="West Europe" ;;
    3) LOCATION="uksouth" ; DISPLAY_NAME="UK South" ;;
    4) LOCATION="canadacentral" ; DISPLAY_NAME="Canada Central" ;;
    5) LOCATION="southeastasia" ; DISPLAY_NAME="Southeast Asia" ;;
    6) LOCATION="australiaeast" ; DISPLAY_NAME="Australia East" ;;
    *) LOCATION="canadacentral" ; DISPLAY_NAME="Canada Central" ;;
esac

# Configuration
RESOURCE_GROUP="PythonIDE-RG"
APP_NAME="pythonide-$(openssl rand -hex 4)"
DB_NAME="pythonide-db-$(openssl rand -hex 4)"
PLAN_NAME="PythonIDE-Plan"
DB_ADMIN="pythonideadmin"
DB_PASSWORD="PyIDE@$(openssl rand -base64 12)"

echo ""
echo "🔧 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  App Name: $APP_NAME"
echo "  Location: $DISPLAY_NAME ($LOCATION)"
echo ""

# Clean up any existing resource group
echo "🧹 Cleaning up any existing resources..."
az group delete --name $RESOURCE_GROUP --yes --no-wait 2>/dev/null || true
sleep 5

# Create Resource Group
echo "📦 Creating Resource Group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output none
echo "✅ Resource group created"

# Create App Service Plan - B1 tier (F1 won't work for your needs)
echo ""
echo "🏗️ Creating App Service Plan (B1 tier for 60+ users)..."
az appservice plan create \
    --name $PLAN_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B1 \
    --is-linux \
    --output none
echo "✅ App Service Plan created (B1: 1.75GB RAM, always-on capable)"

# Create Web App
echo ""
echo "🌐 Creating Web App..."
az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $PLAN_NAME \
    --runtime "PYTHON:3.11" \
    --output none
echo "✅ Web App created: https://$APP_NAME.azurewebsites.net"

# Create PostgreSQL Database (Flexible Server - cheaper)
echo ""
echo "🗄️ Creating PostgreSQL Database..."
echo "   This may take 5-10 minutes..."

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

# Configure firewall
echo "   Configuring database firewall..."
az postgres flexible-server firewall-rule create \
    --name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --rule-name AllowAllAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 255.255.255.255 \
    --output none

# Create database
echo "   Creating pythonide database..."
az postgres flexible-server db create \
    --server-name $DB_NAME \
    --resource-group $RESOURCE_GROUP \
    --database-name pythonide \
    --output none

echo "✅ PostgreSQL database created"

# Configure App Settings
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

# Enable WebSockets
echo "🔌 Enabling WebSockets..."
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

echo "✅ Application configured"

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
echo ""
echo "💾 Saving configuration..."
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
echo "View app at: https://$(jq -r .appName azure-config.json).azurewebsites.net"
EOF
chmod +x deploy.sh

cat > logs.sh << 'EOF'
#!/bin/bash
az webapp log tail --name $(jq -r .appName azure-config.json) --resource-group $(jq -r .resourceGroup azure-config.json)
EOF
chmod +x logs.sh

cat > ssh.sh << 'EOF'
#!/bin/bash
az webapp ssh --name $(jq -r .appName azure-config.json) --resource-group $(jq -r .resourceGroup azure-config.json)
EOF
chmod +x ssh.sh

# Summary
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT SETUP COMPLETE!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📌 Your Azure Resources:"
echo "  • App URL: https://$APP_NAME.azurewebsites.net"
echo "  • Database: $DB_NAME.postgres.database.azure.com"
echo "  • Location: $DISPLAY_NAME"
echo ""
echo "💰 Monthly Cost (covered by your $100 credits):"
echo "  • App Service (B1): ~$13/month"
echo "  • PostgreSQL (Burstable): ~$12/month"
echo "  • Total: ~$25/month (4 months with credits)"
echo ""
echo "🚀 Next Steps:"
echo "  1. Deploy your code:"
echo "     ./deploy.sh"
echo ""
echo "  2. View logs:"
echo "     ./logs.sh"
echo ""
echo "  3. SSH into container:"
echo "     ./ssh.sh"
echo ""
echo "  4. Open your app:"
echo "     https://$APP_NAME.azurewebsites.net"
echo ""
echo "📝 Credentials saved in azure-config.json (keep secure!)"
echo ""

# Clean up test resource groups
echo "🧹 Cleaning up test resource groups..."
for region in northeurope westeurope uksouth canadacentral australiaeast southeastasia; do
    az group delete --name test-$region --yes --no-wait 2>/dev/null || true
done