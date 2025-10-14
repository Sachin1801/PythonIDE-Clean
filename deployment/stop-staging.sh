#!/bin/bash

# Stop Staging Environment

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping staging environment...${NC}"

aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-staging-service \
  --desired-count 0 \
  --region us-east-2 > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Staging stopped (0 tasks running)${NC}"
    echo ""
    echo -e "${YELLOW}💰 Cost while stopped:${NC}"
    echo "  • ECS Fargate: $0.00/hour"
    echo "  • RDS Database: ~$0.02/hour (~$12-14/month)"
    echo ""
    echo -e "${GREEN}Total savings: ~$0.04/hour by stopping ECS${NC}"
else
    echo -e "${RED}❌ Failed to stop service. Check AWS CLI configuration.${NC}"
    exit 1
fi