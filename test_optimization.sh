#!/bin/bash

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Python IDE Optimization Testing${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to wait for server
wait_for_server() {
    echo -e "\n${YELLOW}Waiting for server to be ready...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:10087/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server is ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    echo -e "\n${RED}❌ Server failed to start${NC}"
    return 1
}

# Function to run test
run_test() {
    local test_name=$1
    local processes=$2
    local students=${3:-20}

    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}TEST: $test_name${NC}"
    echo -e "${BLUE}Configuration: TORNADO_PROCESSES=$processes${NC}"
    echo -e "${BLUE}========================================${NC}"

    # Stop any existing containers
    echo -e "\n${YELLOW}Stopping existing containers...${NC}"
    docker-compose -f docker-compose.test.yml down > /dev/null 2>&1

    # Start with configuration
    echo -e "${YELLOW}Starting server with $test_name configuration...${NC}"
    export TEST_TORNADO_PROCESSES=$processes
    docker-compose -f docker-compose.test.yml up -d

    # Wait for server
    if wait_for_server; then
        # Check process count
        echo -e "\n${YELLOW}Checking process count...${NC}"
        docker exec pythonide-test-app ps aux | grep "python server.py" | wc -l

        # Run performance test
        echo -e "\n${YELLOW}Running load test with $students students...${NC}"
        cd tests
        python3 load_test_50_students.py $students
        cd ..

        # Save logs
        echo -e "\n${YELLOW}Saving logs to test_logs_${processes}p.txt...${NC}"
        docker-compose -f docker-compose.test.yml logs > "test_logs_${processes}p.txt" 2>&1
    else
        echo -e "${RED}❌ Test failed - server did not start${NC}"
    fi

    # Stop containers
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    docker-compose -f docker-compose.test.yml down
}

# Main menu
echo -e "\n${YELLOW}Choose test option:${NC}"
echo "1) Quick Test - Compare single vs multi-process (20 students)"
echo "2) Full Test - Compare with 50 students"
echo "3) Single Process Only Test"
echo "4) Multi-Process Only Test"
echo "5) Custom Test"

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo -e "\n${GREEN}Running Quick Comparison Test${NC}"
        run_test "Single-Process" 1 20
        echo -e "\n${YELLOW}Waiting 10 seconds before next test...${NC}"
        sleep 10
        run_test "Multi-Process (2 cores)" 2 20
        ;;
    2)
        echo -e "\n${GREEN}Running Full Comparison Test${NC}"
        run_test "Single-Process" 1 50
        echo -e "\n${YELLOW}Waiting 10 seconds before next test...${NC}"
        sleep 10
        run_test "Multi-Process (2 cores)" 2 50
        ;;
    3)
        run_test "Single-Process" 1 30
        ;;
    4)
        run_test "Multi-Process (2 cores)" 2 30
        ;;
    5)
        read -p "Number of processes (1-4): " procs
        read -p "Number of students (1-100): " students
        run_test "Custom Test" $procs $students
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Testing complete!${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}📊 Summary:${NC}"
echo "- Single-process logs: test_logs_1p.txt"
echo "- Multi-process logs: test_logs_2p.txt (if tested)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review the results above"
echo "2. If multi-process shows improvement, deploy to staging"
echo "3. Monitor staging for 24 hours"
echo "4. Deploy to production if stable"