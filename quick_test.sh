#!/bin/bash

# Quick test script using existing docker-compose.yml

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Quick Multi-Process Test${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}Step 1: Testing with SINGLE process (baseline)${NC}"
echo -e "${YELLOW}Starting server...${NC}"

# Stop any existing containers
docker-compose down 2>/dev/null

# Start with single process
TORNADO_PROCESSES=1 docker-compose up -d

echo -e "${YELLOW}Waiting for server to start (20 seconds)...${NC}"
sleep 20

# Check if server is running
if curl -s http://localhost:10086/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Server started successfully!${NC}"

    # Check logs for process count
    echo -e "\n${YELLOW}Checking process mode...${NC}"
    docker-compose logs | grep "Started Tornado" | tail -1

    echo -e "\n${YELLOW}Running quick load test (10 students)...${NC}"

    # Simple load test with curl
    for i in {1..10}; do
        (
            START=$(date +%s%N)
            curl -s -X POST http://localhost:10086/api/login \
                -H "Content-Type: application/json" \
                -d '{"username":"test_student","password":"test123"}' > /dev/null
            END=$(date +%s%N)
            DIFF=$((($END - $START)/1000000))
            echo "Request $i: ${DIFF}ms"
        ) &
    done
    wait

    echo -e "\n${GREEN}✅ Single-process test complete!${NC}"
else
    echo -e "${RED}❌ Server failed to start${NC}"
    docker-compose logs
    exit 1
fi

# Stop single process
docker-compose down

echo -e "\n${YELLOW}Step 2: Testing with MULTI-PROCESS (2 cores)${NC}"
echo -e "${YELLOW}Starting server with 2 processes...${NC}"

# Start with multi-process
TORNADO_PROCESSES=2 docker-compose up -d

echo -e "${YELLOW}Waiting for server to start (20 seconds)...${NC}"
sleep 20

# Check if server is running
if curl -s http://localhost:10086/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Server started successfully!${NC}"

    # Check logs for process count
    echo -e "\n${YELLOW}Checking process mode...${NC}"
    docker-compose logs | grep "Started Tornado" | tail -1

    echo -e "\n${YELLOW}Running quick load test (10 students)...${NC}"

    # Same load test
    for i in {1..10}; do
        (
            START=$(date +%s%N)
            curl -s -X POST http://localhost:10086/api/login \
                -H "Content-Type: application/json" \
                -d '{"username":"test_student","password":"test123"}' > /dev/null
            END=$(date +%s%N)
            DIFF=$((($END - $START)/1000000))
            echo "Request $i: ${DIFF}ms"
        ) &
    done
    wait

    echo -e "\n${GREEN}✅ Multi-process test complete!${NC}"
else
    echo -e "${RED}❌ Server failed to start${NC}"
    docker-compose logs
fi

# Cleanup
docker-compose down

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Testing complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\nCompare the response times above."
echo -e "If multi-process shows improvement, you can deploy!"