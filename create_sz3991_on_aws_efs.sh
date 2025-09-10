#!/bin/bash

# Script to create sz3991 directory on AWS EFS
# Run this script ON THE AWS ECS CONTAINER or server that has EFS mounted

echo "=========================================="
echo "CREATING SZ3991 DIRECTORY ON AWS EFS"
echo "=========================================="

# Check if EFS is mounted
if [ ! -d "/mnt/efs/pythonide-data" ]; then
    echo "❌ Error: EFS not mounted at /mnt/efs/pythonide-data"
    echo "Expected EFS mount: /mnt/efs/pythonide-data"
    exit 1
fi

echo "✓ EFS mount found at /mnt/efs/pythonide-data"

# Create Local directory structure if it doesn't exist
LOCAL_DIR="/mnt/efs/pythonide-data/ide/Local"
if [ ! -d "$LOCAL_DIR" ]; then
    echo "Creating Local directory structure..."
    mkdir -p "$LOCAL_DIR"
fi

echo "✓ Local directory confirmed: $LOCAL_DIR"

# Create sz3991 user directory
USER_DIR="$LOCAL_DIR/sz3991"
echo "Creating directory: $USER_DIR"

mkdir -p "$USER_DIR"
chmod 755 "$USER_DIR"

# Create welcome file
cat > "$USER_DIR/welcome.py" << 'EOF'
# Welcome to your Python IDE workspace!
# This is Shiwen Zhu's (sz3991) personal directory
# 
# You can:
# - Create Python files (.py)
# - Upload files via the interface
# - Run Python scripts with the Run button
# - Use the hybrid REPL system
# 
# Happy coding! 🐍

print("Hello, Shiwen Zhu!")
print("Welcome to your Python workspace")
print("Your username is: sz3991")
EOF

# Create workspace and submissions subdirectories
mkdir -p "$USER_DIR/workspace"
mkdir -p "$USER_DIR/submissions"

# Set proper permissions
chmod 755 "$USER_DIR"
chmod 644 "$USER_DIR/welcome.py"
chmod 755 "$USER_DIR/workspace"
chmod 755 "$USER_DIR/submissions"

echo "✅ SUCCESS: sz3991 directory created on EFS"
echo ""
echo "📁 Created structure:"
echo "  $USER_DIR/"
echo "  ├── welcome.py"
echo "  ├── workspace/"
echo "  └── submissions/"
echo ""
echo "📋 Verification:"
ls -la "$USER_DIR"
echo ""
echo "🔑 Account ready for: Shiwen Zhu (sz3991)"
echo "Password: EaS08VX%fcp8"