#!/bin/bash

# Quick test script for the multi-user platform
# This script starts the server and runs tests

echo "=================================================="
echo "Quick Test Script for Multi-User Python IDE"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "server.py" ]; then
    cd server 2>/dev/null || { echo -e "${RED}Error: Run this from the server directory${NC}"; exit 1; }
fi

# Activate virtual environment
echo -e "\n${YELLOW}1. Activating virtual environment...${NC}"
source venv/bin/activate || { echo -e "${RED}Failed to activate venv${NC}"; exit 1; }

# Check if database exists
if [ ! -f "ide.db" ]; then
    echo -e "\n${YELLOW}2. Database not found. Creating...${NC}"
    python migrations/create_users.py
fi

# Check if directories exist
if [ ! -d "projects/ide/Local" ]; then
    echo -e "\n${YELLOW}3. Directory structure not found. Creating...${NC}"
    python migrations/setup_directories.py
fi

# Start server in background
echo -e "\n${YELLOW}4. Starting server on port 10086...${NC}"
python server.py --port 10086 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server to start
echo -e "${YELLOW}Waiting for server to start...${NC}"
sleep 3

# Run tests
echo -e "\n${YELLOW}5. Running authentication tests...${NC}"
python test_auth.py

echo -e "\n${YELLOW}6. Want to run comprehensive platform tests? (y/n)${NC}"
read -r response
if [[ "$response" == "y" ]]; then
    python test_platform.py
fi

# Ask if user wants to keep server running
echo -e "\n${YELLOW}Keep server running for manual testing? (y/n)${NC}"
read -r keep_running

if [[ "$keep_running" == "y" ]]; then
    echo -e "\n${GREEN}Server is running on http://localhost:10086${NC}"
    echo -e "${GREEN}Press Ctrl+C to stop the server${NC}"
    
    # Wait for user to stop
    wait $SERVER_PID
else
    # Kill server
    echo -e "\n${YELLOW}Stopping server...${NC}"
    kill $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    echo -e "${GREEN}Server stopped${NC}"
fi

echo -e "\n${GREEN}=================================================="
echo -e "Testing complete!"
echo -e "==================================================${NC}"