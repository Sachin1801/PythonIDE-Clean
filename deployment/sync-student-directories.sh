#!/bin/bash

# Sync student directories to EFS on AWS deployment
set -e

echo "======================================"
echo "SYNCING STUDENT DIRECTORIES TO EFS"  
echo "======================================"

# Check if EFS mount exists
if [ ! -d "/mnt/efs" ]; then
    echo "❌ EFS not mounted at /mnt/efs"
    exit 1
fi

# Ensure base structure exists
mkdir -p /mnt/efs/pythonide-data/ide/Local
mkdir -p /mnt/efs/pythonide-data/ide/Assignments
mkdir -p /mnt/efs/pythonide-data/ide/Tests
mkdir -p "/mnt/efs/pythonide-data/ide/Lecture Notes"

echo "✅ Created base directory structure on EFS"

# Copy student directories from the server/server location (most complete)
if [ -d "/app/server/server/projects/ide/Local" ]; then
    echo "📁 Copying student directories from server/server/projects/ide/Local..."
    cp -r /app/server/server/projects/ide/Local/* /mnt/efs/pythonide-data/ide/Local/
    STUDENT_COUNT=$(ls /mnt/efs/pythonide-data/ide/Local/ | wc -l)
    echo "✅ Copied $STUDENT_COUNT student directories to EFS"
elif [ -d "/app/server/projects/ide/Local" ]; then
    echo "📁 Copying student directories from server/projects/ide/Local..."
    cp -r /app/server/projects/ide/Local/* /mnt/efs/pythonide-data/ide/Local/
    STUDENT_COUNT=$(ls /mnt/efs/pythonide-data/ide/Local/ | wc -l)
    echo "✅ Copied $STUDENT_COUNT student directories to EFS"
else
    echo "⚠️  No source student directories found, will create from database"
fi

echo "======================================"
echo "EFS SYNC COMPLETE"
echo "======================================"

# List what we have
echo "Student directories on EFS:"
ls /mnt/efs/pythonide-data/ide/Local/ | head -10
echo "..."
echo "Total: $(ls /mnt/efs/pythonide-data/ide/Local/ | wc -l) directories"