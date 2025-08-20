#!/bin/bash

# Get the Railway app URL
echo "Testing setup endpoint..."
echo "Replace YOUR_APP_URL with your actual Railway URL"
echo ""
echo "Run this command:"
echo "curl https://YOUR_APP_URL/api/setup"
echo ""
echo "Or if you know your URL:"
read -p "Enter your Railway app URL (e.g., pythonide-production.up.railway.app): " APP_URL

if [ ! -z "$APP_URL" ]; then
    echo "Running setup..."
    curl "https://$APP_URL/api/setup" | python -m json.tool
fi