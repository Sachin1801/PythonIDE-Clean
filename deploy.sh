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
