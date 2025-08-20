# 🚀 Azure Student Deployment Guide

## Quick Start (5 minutes)

### Step 1: Run the Deployment Script
```bash
./azure-student-deploy.sh
```

This script will:
- ✅ Create all Azure resources
- ✅ Setup PostgreSQL database
- ✅ Configure your web app
- ✅ Enable WebSockets
- ✅ Setup monitoring
- ✅ Save credentials to `azure-config.json`

### Step 2: Deploy Your Code
```bash
# First deployment
git add .
git commit -m "Azure deployment setup"
git push azure main:master

# Or use the helper script
./deploy-to-azure.sh
```

### Step 3: Monitor Your App
```bash
# View live logs
./azure-logs.sh

# Or manually
az webapp log tail --name YOUR_APP_NAME --resource-group PythonIDE-Student-RG
```

## 💰 Cost Breakdown with $100 Credits

| Service | Tier | Monthly Cost | What You Get |
|---------|------|--------------|--------------|
| App Service | B1 | ~$13 | 1.75GB RAM, Always on |
| PostgreSQL | Burstable B1ms | ~$12 | 1 vCore, 2GB RAM, 32GB storage |
| Application Insights | Free | $0 | 5GB/month monitoring |
| **Total** | | **~$25/month** | **4 months free with credits** |

## 🎯 Why Azure is Perfect for Your Python IDE

### Reliability
- **99.95% uptime SLA** (vs Railway's no SLA)
- **No sleep timeout** (Railway sleeps after 5 min)
- **Auto-restart on crash**
- **Built-in health checks**

### Performance  
- **1.75GB RAM** (vs Railway's 512MB)
- **Dedicated CPU** (vs shared on Railway)
- **60+ concurrent users** easily supported
- **WebSocket support** built-in

### Database
- **Managed PostgreSQL** with automatic backups
- **Connection pooling** included
- **SSL encryption** by default
- **High availability** options

### Developer Experience
- **GitHub integration** for CI/CD
- **Live logs** and debugging
- **Application Insights** for monitoring
- **VS Code integration** available

## 📊 Monitoring & Management

### View Metrics
```bash
# CPU usage
az monitor metrics list \
  --resource YOUR_APP_NAME \
  --resource-group PythonIDE-Student-RG \
  --metric CpuPercentage \
  --interval PT1M

# Memory usage
az monitor metrics list \
  --resource YOUR_APP_NAME \
  --resource-group PythonIDE-Student-RG \
  --metric MemoryPercentage
```

### Scale Your App
```bash
# Scale up (more resources)
az appservice plan update \
  --name PythonIDE-Student-Plan \
  --resource-group PythonIDE-Student-RG \
  --sku B2  # 3.5GB RAM

# Scale out (more instances)
az webapp scale \
  --name YOUR_APP_NAME \
  --resource-group PythonIDE-Student-RG \
  --instance-count 2
```

## 🔧 Troubleshooting

### WebSocket Issues
```bash
# Verify WebSockets are enabled
az webapp config show \
  --name YOUR_APP_NAME \
  --resource-group PythonIDE-Student-RG \
  --query webSocketsEnabled
```

### Database Connection Issues
```bash
# Test database connection
az postgres flexible-server connect \
  --name YOUR_DB_NAME \
  --admin-user pythonideadmin \
  --admin-password YOUR_PASSWORD
```

### App Not Starting
```bash
# Check startup logs
az webapp log download \
  --name YOUR_APP_NAME \
  --resource-group PythonIDE-Student-RG \
  --log-file startup.log

# SSH into container
az webapp ssh \
  --name YOUR_APP_NAME \
  --resource-group PythonIDE-Student-RG
```

## 🔄 GitHub Actions Setup (Optional)

For automatic deployment on every push:

1. Run the setup script:
```bash
./setup-azure-github-secrets.sh
```

2. Follow the instructions to add the secret to GitHub

3. Update `.github/workflows/azure-deploy.yml` with your app name

4. Push to trigger deployment:
```bash
git push origin main
```

## 📈 Optimization Tips

### 1. Enable Always On
```bash
az webapp config set \
  --name YOUR_APP_NAME \
  --resource-group PythonIDE-Student-RG \
  --always-on true
```

### 2. Configure Auto-Healing
```bash
az webapp config auto-heal update \
  --name YOUR_APP_NAME \
  --resource-group PythonIDE-Student-RG \
  --enabled true \
  --rule type=SlowRequests count=5 timeInterval=30 timeTaken=60
```

### 3. Setup Alerts
```bash
# Alert on high CPU
az monitor metrics alert create \
  --name high-cpu-alert \
  --resource-group PythonIDE-Student-RG \
  --scopes /subscriptions/SUBSCRIPTION_ID/resourceGroups/PythonIDE-Student-RG/providers/Microsoft.Web/sites/YOUR_APP_NAME \
  --condition "avg CpuPercentage > 80" \
  --window-size 5m
```

## 🎓 Student Benefits

With Azure for Students, you also get:
- **$100 credit** renewed annually while you're a student
- **Free services** that don't count against credits:
  - 750 hours B1S Linux App Service
  - 250GB SQL Database
  - 5GB Blob Storage
- **No credit card required**
- **Access to Azure DevOps** free
- **Visual Studio Code** integration

## 📝 Important Files

- `azure-config.json` - Your deployment configuration (keep secure!)
- `deploy-to-azure.sh` - Quick deployment script
- `azure-logs.sh` - View live logs
- `startup.txt` - Azure startup command
- `.azure/config` - Azure CLI configuration

## 🆘 Need Help?

1. **Azure Documentation**: https://docs.microsoft.com/azure
2. **Azure for Students**: https://azure.microsoft.com/free/students
3. **Support**: Use Azure Portal's built-in chat support
4. **Community**: https://stackoverflow.com/questions/tagged/azure

## ✅ Deployment Checklist

- [ ] Run `azure-student-deploy.sh`
- [ ] Note down credentials from `azure-config.json`
- [ ] Deploy code with `./deploy-to-azure.sh`
- [ ] Test WebSocket connections
- [ ] Verify database connectivity
- [ ] Check Application Insights
- [ ] Setup GitHub Actions (optional)
- [ ] Configure custom domain (optional)

---

**Remember**: Your $100 credits give you ~4 months of hosting. After that, you can:
- Apply for Azure credits renewal (if still a student)
- Use GitHub Student Pack for additional credits
- Switch to free tier (with limitations)
- Apply for Microsoft Imagine program through your university