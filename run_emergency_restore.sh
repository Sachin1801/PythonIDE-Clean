#!/bin/bash

echo "==========================================="
echo "EMERGENCY AWS USER RESTORATION"
echo "==========================================="
echo ""

URL="http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com"

echo "⚠️  WARNING: Production database was accidentally cleared!"
echo "This script will restore all 42 users with their correct passwords."
echo ""

echo "Step 1: Upload emergency restore script..."
echo "==========================================="
echo ""
echo "Since we can't access the container directly, we'll use the admin API"
echo ""

# Create a temporary endpoint to run the restoration
cat > restore_via_api.py << 'EOF'
import requests
import json

url = "http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com/api/admin/migrate"

# First check status
print("Checking current status...")
response = requests.get(url)
data = response.json()
print(f"Current users: {data['total_users']}")
print("")

# Run migration with hardcoded users
print("Running emergency restoration...")
payload = {"secret": "PythonIDE2025Migration", "emergency_restore": True}
response = requests.post(url, json=payload)
data = response.json()

if data.get('success'):
    print("✅ Restoration successful!")
    print(f"Total users: {data.get('total_users', 0)}")
else:
    print("❌ Restoration failed!")
    print(f"Error: {data.get('error', 'Unknown error')}")

# Test login
print("\nTesting admin_editor login...")
login_data = {"username": "admin_editor", "password": "XuR0ibQqhw6#"}
response = requests.post(f"{url.replace('/api/admin/migrate', '/api/login')}", json=login_data)
if response.json().get('success'):
    print("✅ Login successful!")
else:
    print("❌ Login failed!")
EOF

echo "Running restoration via API..."
python3 restore_via_api.py

echo ""
echo "==========================================="
echo "Alternative: Manual Database Commands"
echo "==========================================="
echo ""
echo "If the API method fails, you'll need to:"
echo "1. Get database access credentials"
echo "2. Connect directly to the RDS PostgreSQL instance"
echo "3. Run the emergency_restore_users.py script locally"
echo ""
echo "Database endpoint: pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com"
echo "Database name: pythonide"
echo ""
echo "To connect locally with the script:"
echo "export DATABASE_URL=postgresql://pythonide_admin:Sachinadlakha9082@pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432/pythonide"
echo "python emergency_restore_users.py"
echo ""