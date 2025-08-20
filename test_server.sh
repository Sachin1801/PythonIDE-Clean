#!/bin/bash

echo "Testing Python IDE Server with fixes..."
echo "======================================="

# Navigate to server directory
cd server

# Activate virtual environment
source venv/bin/activate

# Test the server
echo "Starting server on port 10086..."
python server.py --port 10086