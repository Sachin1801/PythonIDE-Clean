#!/bin/bash

# Script to update ECS service with proper deployment configuration
# This prevents multiple tasks from running simultaneously

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-2}
ECS_CLUSTER=${ECS_CLUSTER:-pythonide-cluster}
ECS_SERVICE=${ECS_SERVICE:-pythonide-service}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Updating ECS Service Deployment Configuration...${NC}"

# Update service with deployment configuration to prevent multiple tasks
echo -e "${YELLOW}Setting deployment configuration...${NC}"
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --deployment-configuration \
        "maximumPercent=100,minimumHealthyPercent=0,deploymentCircuitBreaker={rollback=true,enable=true}" \
    --region ${AWS_REGION}

echo -e "${GREEN}Deployment configuration updated!${NC}"
echo -e "- Maximum percent: 100% (prevents multiple tasks)"
echo -e "- Minimum healthy: 0% (allows old task to stop before new one starts)"
echo -e "- Circuit breaker: Enabled (auto-rollback on failures)"

# Optional: Force a new deployment with the updated configuration
read -p "Do you want to force a new deployment now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Forcing new deployment...${NC}"
    aws ecs update-service \
        --cluster ${ECS_CLUSTER} \
        --service ${ECS_SERVICE} \
        --force-new-deployment \
        --region ${AWS_REGION}
    
    echo -e "${GREEN}New deployment started!${NC}"
    echo -e "Monitor progress in the AWS ECS console"
fi