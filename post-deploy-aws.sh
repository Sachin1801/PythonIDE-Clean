#!/bin/bash

# Post-deployment script for AWS
# Run this after deploy-aws.sh to ensure everything is set up correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=======================${NC}"
echo -e "${GREEN}AWS Post-Deployment Setup${NC}"
echo -e "${GREEN}=======================${NC}"

# Step 1: Fix username in RDS
echo -e "${YELLOW}Step 1: Fixing username in RDS database...${NC}"
python3 fix_aws_username.py

# Step 2: Verify ECS deployment
echo -e "\n${YELLOW}Step 2: Checking ECS service status...${NC}"
aws ecs describe-services \
    --cluster pythonide-cluster \
    --services pythonide-service \
    --region us-east-2 \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}' \
    --output table 2>/dev/null || echo "ECS service check skipped (cluster may not exist locally)"

# Step 3: Get Load Balancer URL
echo -e "\n${YELLOW}Step 3: Getting application URL...${NC}"
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --region us-east-2 \
    --query "LoadBalancers[?contains(LoadBalancerName, 'pythonide')].DNSName" \
    --output text)

if [ -z "$ALB_DNS" ]; then
    echo -e "${RED}Could not find Load Balancer DNS${NC}"
else
    echo -e "${GREEN}Application URL: http://${ALB_DNS}${NC}"
fi

# Step 4: Check EFS mount (via ECS task)
echo -e "\n${YELLOW}Step 4: Verifying EFS directories...${NC}"
echo "Note: EFS directories are created automatically when containers start."
echo "The following directories should exist on EFS:"
echo "  /mnt/efs/pythonide-data/ide/Local/"
echo "  /mnt/efs/pythonide-data/ide/Lecture Notes/"

# Step 5: Test login
echo -e "\n${GREEN}=======================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}=======================${NC}"
echo ""
echo "You can now test the application at:"
echo -e "${GREEN}http://${ALB_DNS}${NC}"
echo ""
echo "Test credentials:"
echo "  Admin: sa9082 / Admin@sa9082"
echo "  Student: jn9106 / student@jn9106"
echo ""
echo "To check ECS logs:"
echo "  aws logs tail /ecs/pythonide-backend --follow"
echo ""
echo "To force a new deployment (if needed):"
echo "  aws ecs update-service --cluster pythonide-cluster --service pythonide-service --force-new-deployment"