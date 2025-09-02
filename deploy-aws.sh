#!/bin/bash

# AWS Deployment Script for PythonIDE
# Make sure to set these environment variables first!

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
ECR_REPOSITORY=${ECR_REPOSITORY:-pythonide-backend}
ECS_CLUSTER=${ECS_CLUSTER:-pythonide-cluster}
ECS_SERVICE=${ECS_SERVICE:-pythonide-service}
S3_BUCKET=${S3_BUCKET}
CLOUDFRONT_DISTRIBUTION_ID=${CLOUDFRONT_DISTRIBUTION_ID}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AWS Deployment...${NC}"

# Check required variables
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: AWS_ACCOUNT_ID not set${NC}"
    exit 1
fi

if [ -z "$S3_BUCKET" ]; then
    echo -e "${RED}Error: S3_BUCKET not set${NC}"
    exit 1
fi

# Step 1: Build Backend Docker Image
echo -e "${YELLOW}Building backend Docker image...${NC}"
docker build -f Dockerfile.backend -t ${ECR_REPOSITORY}:latest .

# Step 2: Authenticate Docker to ECR
echo -e "${YELLOW}Authenticating with ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Step 3: Tag and Push Backend Image
echo -e "${YELLOW}Pushing backend image to ECR...${NC}"
docker tag ${ECR_REPOSITORY}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest

# Step 4: Build Frontend
echo -e "${YELLOW}Building frontend...${NC}"
npm run build

# Step 5: Deploy Frontend to S3
echo -e "${YELLOW}Deploying frontend to S3...${NC}"
aws s3 sync dist/ s3://${S3_BUCKET} --delete

# Step 6: Invalidate CloudFront cache (if distribution ID provided)
if [ ! -z "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo -e "${YELLOW}Invalidating CloudFront cache...${NC}"
    aws cloudfront create-invalidation \
        --distribution-id ${CLOUDFRONT_DISTRIBUTION_ID} \
        --paths "/*"
fi

# Step 7: Update ECS Service (force new deployment)
echo -e "${YELLOW}Updating ECS service...${NC}"
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --force-new-deployment \
    --region ${AWS_REGION}

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Backend: Check ECS console for service status"
echo -e "Frontend: https://${S3_BUCKET}.s3-website-${AWS_REGION}.amazonaws.com"