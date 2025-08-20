# Azure Deployment Guide for Python IDE

## Prerequisites
- Azure account with $100 free credits
- Azure CLI installed (`curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`)

## Step 1: Azure Setup

```bash
# Login to Azure
az login

# Create resource group
az group create --name PythonIDE-RG --location eastus

# Create App Service Plan (Free tier F1 or Basic B1)
az appservice plan create \
  --name PythonIDE-Plan \
  --resource-group PythonIDE-RG \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --name pythonide-app \
  --resource-group PythonIDE-RG \
  --plan PythonIDE-Plan \
  --runtime "PYTHON:3.11"

# Create PostgreSQL server
az postgres server create \
  --name pythonide-db \
  --resource-group PythonIDE-RG \
  --sku-name B_Gen5_1 \
  --admin-user dbadmin \
  --admin-password "YourSecurePassword123!" \
  --location eastus

# Create database
az postgres db create \
  --name pythonide \
  --resource-group PythonIDE-RG \
  --server-name pythonide-db

# Configure firewall for Azure services
az postgres server firewall-rule create \
  --resource-group PythonIDE-RG \
  --server-name pythonide-db \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

## Step 2: Configure Application Settings

```bash
# Set environment variables
az webapp config appsettings set \
  --name pythonide-app \
  --resource-group PythonIDE-RG \
  --settings \
    DATABASE_URL="postgresql://dbadmin@pythonide-db:YourSecurePassword123!@pythonide-db.postgres.database.azure.com:5432/pythonide?sslmode=require" \
    IDE_SECRET_KEY="your-secret-key-here" \
    MAX_CONCURRENT_EXECUTIONS=60 \
    EXECUTION_TIMEOUT=30 \
    MEMORY_LIMIT_MB=256 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    WEBSITES_PORT=8080

# Configure startup command
az webapp config set \
  --name pythonide-app \
  --resource-group PythonIDE-RG \
  --startup-file "startup.sh"
```

## Step 3: Deploy with Git

```bash
# Configure deployment credentials
az webapp deployment user set \
  --user-name pythonide-deploy \
  --password "DeployPassword123!"

# Get deployment URL
az webapp deployment source config-local-git \
  --name pythonide-app \
  --resource-group PythonIDE-RG

# Add Azure as git remote
git remote add azure https://pythonide-deploy@pythonide-app.scm.azurewebsites.net/pythonide-app.git

# Deploy
git push azure main:master
```

## Step 4: Enable WebSockets

```bash
az webapp config set \
  --name pythonide-app \
  --resource-group PythonIDE-RG \
  --web-sockets-enabled true
```

## Step 5: Setup Monitoring

```bash
# Create Application Insights
az monitor app-insights component create \
  --app pythonide-insights \
  --location eastus \
  --resource-group PythonIDE-RG

# Get instrumentation key
az monitor app-insights component show \
  --app pythonide-insights \
  --resource-group PythonIDE-RG \
  --query instrumentationKey
```

## Step 6: Scale Configuration (Optional)

```bash
# Enable auto-scaling
az monitor autoscale create \
  --resource-group PythonIDE-RG \
  --resource pythonide-app \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscale-config \
  --min-count 1 \
  --max-count 3 \
  --count 1

# Add scale rule based on CPU
az monitor autoscale rule create \
  --resource-group PythonIDE-RG \
  --autoscale-name autoscale-config \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1
```

## URLs After Deployment
- App: https://pythonide-app.azurewebsites.net
- Kudu Console: https://pythonide-app.scm.azurewebsites.net
- Database: pythonide-db.postgres.database.azure.com

## Cost Breakdown (Monthly)
With $100 credits, you get approximately 2-3 months of:
- B1 App Service: ~$13/month
- Basic PostgreSQL: ~$25/month  
- Application Insights: Free tier (5GB/month)
- Storage: Free tier (5GB)
Total: ~$38/month

## Monitoring Commands

```bash
# View logs
az webapp log tail \
  --name pythonide-app \
  --resource-group PythonIDE-RG

# Check metrics
az monitor metrics list \
  --resource pythonide-app \
  --resource-group PythonIDE-RG \
  --resource-type Microsoft.Web/sites \
  --metric CpuPercentage

# Restart app
az webapp restart \
  --name pythonide-app \
  --resource-group PythonIDE-RG
```