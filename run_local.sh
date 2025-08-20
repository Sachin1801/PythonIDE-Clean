#!/bin/bash

echo "🚀 Starting PythonIDE in LOCAL development mode..."
echo ""

# Kill any existing processes on the ports
echo "📋 Checking for existing processes..."
lsof -ti:10086 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start backend server
echo "🔧 Starting backend server on port 10086..."
cd server
python server.py --port 10086 &
BACKEND_PID=$!
cd ..

# Give backend time to start
sleep 2

# Start frontend dev server
echo "🎨 Starting frontend dev server on port 8080..."
npm run serve &
FRONTEND_PID=$!

echo ""
echo "✅ Local development servers started!"
echo ""
echo "📍 Access the application at: http://localhost:8080"
echo "📍 Backend API running at: http://localhost:10086"
echo ""
echo "🔄 Frontend will auto-reload on changes"
echo "⚠️  Backend requires manual restart for Python changes"
echo ""
echo "Press Ctrl+C to stop all servers..."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    lsof -ti:10086 | xargs kill -9 2>/dev/null
    lsof -ti:8080 | xargs kill -9 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set up trap to cleanup on Ctrl+C
trap cleanup INT

# Wait for processes
wait