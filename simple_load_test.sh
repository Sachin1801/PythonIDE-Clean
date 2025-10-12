#!/bin/bash

# Simple load test using curl (no Python dependencies needed)

NUM_REQUESTS=${1:-20}
URL="http://localhost:10086"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🧪 Running load test with $NUM_REQUESTS concurrent requests${NC}"
echo ""

# Store response times
RESPONSE_TIMES=()

# Run concurrent requests
for i in $(seq 1 $NUM_REQUESTS); do
    (
        START=$(date +%s%N)
        RESPONSE=$(curl -s -X POST "$URL/api/login" \
            -H "Content-Type: application/json" \
            -d "{\"username\":\"test_student_$i\",\"password\":\"test123\"}" \
            -w "%{http_code}" \
            -o /dev/null 2>/dev/null)
        END=$(date +%s%N)

        DURATION=$((($END - $START) / 1000000))  # Convert to milliseconds

        if [ "$RESPONSE" == "200" ] || [ "$RESPONSE" == "401" ]; then
            echo "$DURATION ms - Request $i completed (HTTP $RESPONSE)"
        else
            echo "$DURATION ms - Request $i FAILED (HTTP $RESPONSE)"
        fi

        echo "$DURATION" >> /tmp/load_test_results.txt
    ) &
done

# Wait for all requests to complete
wait

echo ""
echo -e "${GREEN}✅ All requests completed${NC}"
echo ""

# Calculate statistics
if [ -f /tmp/load_test_results.txt ]; then
    TIMES=($(cat /tmp/load_test_results.txt | sort -n))
    COUNT=${#TIMES[@]}

    # Calculate average
    SUM=0
    for time in "${TIMES[@]}"; do
        SUM=$((SUM + time))
    done
    AVG=$((SUM / COUNT))

    # Get min, max, median
    MIN=${TIMES[0]}
    MAX=${TIMES[$((COUNT-1))]}
    MEDIAN=${TIMES[$((COUNT/2))]}

    # Get 95th percentile
    P95_IDX=$(((COUNT * 95) / 100))
    P95=${TIMES[$P95_IDX]}

    echo -e "${YELLOW}📊 Results:${NC}"
    echo "  Total requests: $COUNT"
    echo "  Average: ${AVG}ms"
    echo "  Median: ${MEDIAN}ms"
    echo "  Min: ${MIN}ms"
    echo "  Max: ${MAX}ms"
    echo "  95th percentile: ${P95}ms"
    echo ""

    # Assessment
    if [ $AVG -lt 100 ]; then
        echo -e "${GREEN}🎉 EXCELLENT performance!${NC}"
    elif [ $AVG -lt 300 ]; then
        echo -e "${GREEN}✅ GOOD performance${NC}"
    elif [ $AVG -lt 1000 ]; then
        echo -e "${YELLOW}⚠️ ACCEPTABLE performance${NC}"
    else
        echo -e "${RED}❌ POOR performance - optimization needed${NC}"
    fi

    # Cleanup
    rm /tmp/load_test_results.txt
fi