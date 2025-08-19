#!/bin/bash

echo "=================================================="
echo "Starting Python IDE with Authentication"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Kill any existing processes on the ports
echo -e "\n${YELLOW}Cleaning up existing processes...${NC}"
lsof -ti:10086 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start backend server
echo -e "\n${YELLOW}Starting backend server on port 10086...${NC}"
cd server
source venv/bin/activate
python server.py --port 10086 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo -e "${YELLOW}Waiting for backend to start...${NC}"
sleep 3

# Start frontend dev server
echo -e "\n${YELLOW}Starting frontend dev server on port 8080...${NC}"
npm run serve &
FRONTEND_PID=$!

# Wait for frontend to start
echo -e "${YELLOW}Waiting for frontend to start...${NC}"
sleep 5

echo -e "\n${GREEN}=================================================="
echo -e "✅ Both servers are running!"
echo -e "=================================================="
echo -e "${NC}"
echo "Backend API: http://localhost:10086"
echo "Frontend UI: http://localhost:8080"
echo ""
echo "Test Credentials:"
echo "  Student: sa9082 / sa90822024"
echo "  Professor: professor / ChangeMeASAP2024!"
echo ""
echo "To test:"
echo "1. Open http://localhost:8080 in your browser"
echo "2. Click 'Sign In' button"
echo "3. Enter credentials above"
echo "4. You should see only your authorized files"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait