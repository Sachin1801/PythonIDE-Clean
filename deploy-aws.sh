#!/bin/bash

# AWS Deployment Script for PythonIDE
# Make sure to set these environment variables first!

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-2}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
ECR_REPOSITORY=${ECR_REPOSITORY:-pythonide-backend}
ECS_CLUSTER=${ECS_CLUSTER:-pythonide-cluster}
ECS_SERVICE=${ECS_SERVICE:-pythonide-service}
# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AWS Deployment (Combined Frontend + Backend)...${NC}"

# Check required variables
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: AWS_ACCOUNT_ID not set${NC}"
    exit 1
fi

# Step 1: Build Combined Docker Image (Frontend + Backend)
echo -e "${YELLOW}Building Docker image (combined frontend + backend)...${NC}"
docker build --platform linux/amd64 -f Dockerfile -t ${ECR_REPOSITORY}:latest .

# Step 2: Authenticate Docker to ECR
echo -e "${YELLOW}Authenticating with ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Step 3: Tag and Push Combined Image
echo -e "${YELLOW}Pushing Docker image to ECR...${NC}"
docker tag ${ECR_REPOSITORY}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest

# Step 4: Update ECS Service (force new deployment)
echo -e "${YELLOW}Updating ECS service...${NC}"
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --force-new-deployment \
    --region ${AWS_REGION}

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Application: Check ECS console for service status"
echo -e "Access URL: Check your Load Balancer or ECS service endpoint"