#!/bin/bash
# Quick local test script for security fix (without Docker)

echo "🧪 Testing Security Fix Locally (without Docker)"
echo "================================================"
echo ""

# Check if server is running
if lsof -Pi :10086 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Server is running on port 10086"
else
    echo "❌ Server is NOT running on port 10086"
    echo ""
    echo "To start the server, run:"
    echo "  cd /Users/sachin/Desktop/Projects/PythonIDE-Clean"
    echo "  uv run python server/server.py --port 10086"
    echo ""
    exit 1
fi

echo ""
echo "📝 Next steps:"
echo "1. Open browser: http://localhost:10086"
echo "2. Login with a student account (e.g., sa9082, test_student)"
echo "3. Create a new Python file in Local/{username}/"
echo "4. Copy test_security_fix.py content into it"
echo "5. Run the script and verify output"
echo ""
echo "Expected results:"
echo "  - Tests 1-8: ✅ BLOCKED (PermissionError)"
echo "  - Test 9-10: ✅ SUCCESS"
echo ""
