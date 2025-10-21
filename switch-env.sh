#!/bin/bash
# Script to switch between main and exam environments

if [ "$1" == "main" ]; then
    echo "🔄 Switching to MAIN IDE environment (port 10086)..."
    cp .env.development.main .env.development
    echo "✅ Frontend will now connect to: ws://localhost:10086"
    echo "📝 Restart your frontend (npm run serve) for changes to take effect"
elif [ "$1" == "exam" ]; then
    echo "🔄 Switching to EXAM IDE environment (port 10087)..."
    cp .env.development.exam .env.development
    echo "✅ Frontend will now connect to: ws://localhost:10087"
    echo "📝 Restart your frontend (npm run serve) for changes to take effect"
else
    echo "Usage: ./switch-env.sh [main|exam]"
    echo ""
    echo "Examples:"
    echo "  ./switch-env.sh main    # Switch to main IDE (port 10086)"
    echo "  ./switch-env.sh exam    # Switch to exam IDE (port 10087)"
    echo ""
    echo "Current configuration:"
    grep "VUE_APP_WS_PORT" .env.development
fi
