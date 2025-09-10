#!/bin/bash

echo "=========================================="
echo "AWS MIGRATION - COMMAND LINE VERSION"
echo "=========================================="
echo ""

URL="http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com"

echo "Step 1: Checking current status..."
echo "----------------------------------------"
curl -X GET "${URL}/api/admin/migrate" 2>/dev/null | python3 -m json.tool

echo ""
echo "Step 2: Running migration..."
echo "----------------------------------------"
echo "This will create all 42 users with production passwords."
read -p "Enter 'yes' to continue: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Migration cancelled."
    exit 1
fi

echo ""
echo "Sending migration request with secret..."
RESPONSE=$(curl -X POST "${URL}/api/admin/migrate" \
  -H "Content-Type: application/json" \
  -d '{"secret":"PythonIDE2025Migration"}' \
  2>/dev/null)

echo "Response:"
echo "$RESPONSE" | python3 -m json.tool

echo ""
echo "=========================================="
echo "Step 3: Testing login..."
echo "----------------------------------------"
echo "Testing admin_editor login..."

LOGIN_RESPONSE=$(curl -X POST "${URL}/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_editor","password":"XuR0ibQqhw6#"}' \
  2>/dev/null)

echo "Login response:"
echo "$LOGIN_RESPONSE" | python3 -m json.tool

echo ""
echo "=========================================="
echo "MIGRATION COMPLETE!"
echo "=========================================="
echo ""
echo "Admin Credentials:"
echo "  admin_editor: XuR0ibQqhw6#"
echo "  sa9082: pXzwjLIYE20*"
echo "  sl7927: 4qPg1cmJkUa!"
echo "  et2434: evaTQRwfyhC*"
echo ""
echo "URLs:"
echo "  Main App: ${URL}"
echo "  Admin Panel: ${URL}/admin/users"
echo ""