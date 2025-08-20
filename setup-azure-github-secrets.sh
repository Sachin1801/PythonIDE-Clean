#!/bin/bash

# Script to set up GitHub secrets for Azure deployment

echo "Setting up GitHub Secrets for Azure Deployment"
echo "=============================================="
echo ""

# Check if azure-config.json exists
if [ ! -f "azure-config.json" ]; then
    echo "❌ azure-config.json not found. Please run azure-student-deploy.sh first."
    exit 1
fi

# Read configuration
APP_NAME=$(jq -r .appName azure-config.json)
RESOURCE_GROUP=$(jq -r .resourceGroup azure-config.json)

echo "📝 Creating Service Principal for GitHub Actions..."

# Create service principal
SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "PythonIDE-GitHub-Actions" \
    --role contributor \
    --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP \
    --sdk-auth)

echo ""
echo "✅ Service Principal created!"
echo ""
echo "═══════════════════════════════════════════════════════"
echo "📋 GITHUB SECRETS SETUP"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "1. Go to your GitHub repository:"
echo "   https://github.com/YOUR_USERNAME/PythonIDE-Clean/settings/secrets/actions"
echo ""
echo "2. Click 'New repository secret'"
echo ""
echo "3. Create a secret named: AZURE_CREDENTIALS"
echo "   Value (copy everything between the lines):"
echo "-------------------------------------------"
echo "$SP_OUTPUT"
echo "-------------------------------------------"
echo ""
echo "4. Update .github/workflows/azure-deploy.yml:"
echo "   Change AZURE_WEBAPP_NAME to: $APP_NAME"
echo ""
echo "5. Commit and push to trigger deployment:"
echo "   git add ."
echo "   git commit -m 'Setup Azure deployment'"
echo "   git push origin main"
echo ""
echo "✅ After setting up the secret, GitHub Actions will automatically deploy on push!"