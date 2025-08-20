#!/bin/bash

# Direct Azure deployment with westus2 (most reliable for students)

set -e

echo "═══════════════════════════════════════════════════════"
echo "   Azure Student Deployment - Direct Method"
echo "   Using westus2 region (best for students)"
echo "═══════════════════════════════════════════════════════"
echo ""

# Configuration - using westus2 which works for most students
RESOURCE_GROUP="PythonIDE-RG-$(openssl rand -hex 4)"
LOCATION="westus2"  # Most reliable for students
APP_NAME="pythonide-$(openssl rand -hex 4)"
PLAN_NAME="pythonide-plan-$(openssl rand -hex 4)"

echo "🔧 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  App Name: $APP_NAME"
echo "  Location: $LOCATION (West US 2)"
echo ""

# Check login
if ! az account show &>/dev/null; then
    echo "📝 Please login using device code..."
    az login --use-device-code
fi

echo "✅ Logged in successfully"
echo ""

# Try to create resources one by one
echo "Creating resources in $LOCATION..."
echo ""

# 1. Resource Group
echo "1️⃣ Creating Resource Group..."
if az group create --name $RESOURCE_GROUP --location $LOCATION --output none; then
    echo "   ✅ Resource group created"
else
    echo "   ❌ Failed to create resource group"
    exit 1
fi

# 2. Try different SKUs in order of preference
echo "2️⃣ Creating App Service Plan..."
SKUS=("F1" "B1" "S1")
PLAN_CREATED=false

for SKU in "${SKUS[@]}"; do
    echo "   Trying $SKU tier..."
    if az appservice plan create \
        --name $PLAN_NAME \
        --resource-group $RESOURCE_GROUP \
        --sku $SKU \
        --is-linux \
        --output none 2>/dev/null; then
        echo "   ✅ App Service Plan created with $SKU tier"
        PLAN_CREATED=true
        break
    fi
done

if [ "$PLAN_CREATED" = false ]; then
    echo "   ❌ Could not create App Service Plan"
    echo ""
    echo "Try these alternative regions:"
    echo "  • westus"
    echo "  • centralus"
    echo "  • southcentralus"
    exit 1
fi

# 3. Web App
echo "3️⃣ Creating Web App..."
if az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $PLAN_NAME \
    --runtime "PYTHON:3.11" \
    --output none; then
    echo "   ✅ Web App created"
else
    echo "   ❌ Failed to create Web App"
    exit 1
fi

# 4. Configure Web App
echo "4️⃣ Configuring Web App..."

# Enable WebSockets
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --web-sockets-enabled true \
    --output none

# Set app settings
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
    --output none

# Set startup command
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "cd server && python server.py" \
    --output none

echo "   ✅ Web App configured"

# 5. Setup deployment
echo "5️⃣ Setting up deployment..."

# Get deployment URL
DEPLOYMENT_URL=$(az webapp deployment source config-local-git \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query url \
    --output tsv)

# Add git remote
git remote remove azure 2>/dev/null || true
git remote add azure $DEPLOYMENT_URL

echo "   ✅ Deployment configured"

# Save configuration
cat > azure-config.json << EOF
{
    "resourceGroup": "$RESOURCE_GROUP",
    "appName": "$APP_NAME",
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
EOF
chmod +x deploy.sh

cat > logs.sh << 'EOF'
#!/bin/bash
APP=$(jq -r .appName azure-config.json)
RG=$(jq -r .resourceGroup azure-config.json)
az webapp log tail --name $APP --resource-group $RG
EOF
chmod +x logs.sh

# Success message
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📌 Your app details:"
echo "  • URL: https://$APP_NAME.azurewebsites.net"
echo "  • Region: $LOCATION"
echo "  • Resource Group: $RESOURCE_GROUP"
echo ""
echo "🚀 Next steps:"
echo "  1. Deploy code: ./deploy.sh"
echo "  2. View logs: ./logs.sh"
echo "  3. Open app: https://$APP_NAME.azurewebsites.net"
echo ""
echo "💡 If this region doesn't work, try editing the script"
echo "   and change LOCATION to: westus, centralus, or southcentralus"