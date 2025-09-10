#!/bin/bash

echo "==========================================="
echo "FIX EFS DIRECTORIES ON AWS PRODUCTION"
echo "==========================================="
echo ""

# Use both URLs to ensure we can connect
URLS=(
    "http://pythonide-classroom.tech"
    "http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com"
)

# Try each URL until one works
for URL in "${URLS[@]}"; do
    echo "Trying URL: $URL"
    echo "-----------------------------------------"
    
    # Test connection
    if curl -s -o /dev/null -w "%{http_code}" "$URL/health" | grep -q "200"; then
        echo "✓ Connected to $URL"
        
        echo ""
        echo "Running directory fix..."
        echo "-----------------------------------------"
        
        RESPONSE=$(curl -X POST "$URL/api/admin/migrate" \
          -H "Content-Type: application/json" \
          -d '{
            "secret": "PythonIDE2025Migration",
            "action": "fix_directories"
          }' \
          2>/dev/null)
        
        echo "Response:"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
        
        echo ""
        echo "==========================================="
        echo "DIRECTORY FIX COMPLETE!"
        echo "==========================================="
        echo ""
        echo "To verify, log in as any user and check their Local/ directory"
        echo "URL: $URL"
        
        break
    else
        echo "✗ Could not connect to $URL"
    fi
done

echo ""
echo "Admin credentials for testing:"
echo "  Username: admin_editor"
echo "  Password: XuR0ibQqhw6#"
echo ""