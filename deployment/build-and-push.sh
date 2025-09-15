#!/bin/bash

# Script to build and push Docker image to ECR

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-2}
AWS_ACCOUNT_ID=653306034507
ECR_REPOSITORY=pythonide-backend

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Building and Pushing Docker Image to ECR${NC}"

# Step 1: Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ${ECR_REPOSITORY}:latest .

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker image built successfully${NC}"

# Step 2: Authenticate with ECR
echo -e "${YELLOW}Authenticating with ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

if [ $? -ne 0 ]; then
    echo -e "${RED}ECR authentication failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Authenticated with ECR${NC}"

# Step 3: Tag the image
echo -e "${YELLOW}Tagging image...${NC}"
docker tag ${ECR_REPOSITORY}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest

# Step 4: Push to ECR
echo -e "${YELLOW}Pushing image to ECR...${NC}"
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker push failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Image pushed successfully${NC}"

# Step 5: Force new deployment
echo -e "${YELLOW}Forcing new deployment...${NC}"
aws ecs update-service \
    --cluster pythonide-cluster \
    --service pythonide-service \
    --force-new-deployment \
    --desired-count 1 \
    --region ${AWS_REGION} \
    --output text > /dev/null

echo -e "${GREEN}✓ Deployment triggered${NC}"

# Step 6: Wait and check status
echo -e "${YELLOW}Waiting for deployment to start (30 seconds)...${NC}"
sleep 30

# Check service status
aws ecs describe-services \
    --cluster pythonide-cluster \
    --services pythonide-service \
    --query 'services[0].{RunningTasks:runningCount,PendingTasks:pendingCount,DesiredTasks:desiredCount}' \
    --output table \
    --region ${AWS_REGION}

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${YELLOW}Monitor progress:${NC}"
echo "aws ecs describe-services --cluster pythonide-cluster --services pythonide-service --region ${AWS_REGION}"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo "aws logs tail /ecs/pythonide --follow --region ${AWS_REGION}"
echo ""
echo -e "${YELLOW}Access URL:${NC}"
echo "http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com"