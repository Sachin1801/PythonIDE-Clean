@echo off
echo Deploying Python IDE to Azure...

:: Install Python dependencies
cd server
pip install -r requirements.txt

:: Build frontend
cd ..
npm install
npm run build

:: Copy startup script
copy azure-startup.sh %DEPLOYMENT_TARGET%\startup.sh

echo Deployment complete!