#!/bin/bash
# Build script for Railway

# Install frontend dependencies and build
echo "Building frontend..."
npm install
npm run build

# Install backend dependencies
echo "Installing backend dependencies..."
cd server
pip install -r requirements.txt || python -m pip install -r requirements.txt || python3 -m pip install -r requirements.txt

echo "Build complete!"