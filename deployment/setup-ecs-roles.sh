#!/bin/bash

# Script to create or find ECS Task Execution and Task roles

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-2}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up ECS IAM Roles...${NC}"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "AWS Account ID: ${AWS_ACCOUNT_ID}"

# Check if ecsTaskExecutionRole exists
echo -e "${YELLOW}Checking for existing ecsTaskExecutionRole...${NC}"
EXECUTION_ROLE_ARN=$(aws iam get-role --role-name ecsTaskExecutionRole --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$EXECUTION_ROLE_ARN" ]; then
    echo -e "${YELLOW}Creating ecsTaskExecutionRole...${NC}"
    
    # Create trust policy
    cat > /tmp/ecs-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create the execution role
    aws iam create-role \
        --role-name ecsTaskExecutionRole \
        --assume-role-policy-document file:///tmp/ecs-trust-policy.json \
        --region ${AWS_REGION}
    
    # Attach the managed policy
    aws iam attach-role-policy \
        --role-name ecsTaskExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
        --region ${AWS_REGION}
    
    EXECUTION_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole"
    echo -e "${GREEN}✓ Created ecsTaskExecutionRole${NC}"
else
    echo -e "${GREEN}✓ Found existing ecsTaskExecutionRole${NC}"
fi

# Check if ecsTaskRole exists (for EFS access)
echo -e "${YELLOW}Checking for existing ecsTaskRole...${NC}"
TASK_ROLE_ARN=$(aws iam get-role --role-name ecsTaskRole --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$TASK_ROLE_ARN" ]; then
    echo -e "${YELLOW}Creating ecsTaskRole with EFS permissions...${NC}"
    
    # Create the task role
    aws iam create-role \
        --role-name ecsTaskRole \
        --assume-role-policy-document file:///tmp/ecs-trust-policy.json \
        --region ${AWS_REGION}
    
    # Create EFS policy
    cat > /tmp/efs-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "elasticfilesystem:ClientMount",
        "elasticfilesystem:ClientWrite",
        "elasticfilesystem:DescribeFileSystems",
        "elasticfilesystem:DescribeMountTargets"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOF

    # Create and attach the policy
    aws iam put-role-policy \
        --role-name ecsTaskRole \
        --policy-name EFSAccessPolicy \
        --policy-document file:///tmp/efs-policy.json \
        --region ${AWS_REGION}
    
    # Also attach policy for ECS Exec (for debugging)
    aws iam attach-role-policy \
        --role-name ecsTaskRole \
        --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore \
        --region ${AWS_REGION}
    
    TASK_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskRole"
    echo -e "${GREEN}✓ Created ecsTaskRole with EFS permissions${NC}"
else
    echo -e "${GREEN}✓ Found existing ecsTaskRole${NC}"
    
    # Ensure ECS Exec policy is attached (for debugging)
    echo -e "${YELLOW}Ensuring ECS Exec policy is attached...${NC}"
    aws iam attach-role-policy \
        --role-name ecsTaskRole \
        --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore \
        --region ${AWS_REGION} 2>/dev/null || true
fi

# Clean up temp files
rm -f /tmp/ecs-trust-policy.json /tmp/efs-policy.json

echo -e "${GREEN}=== IAM Roles Ready ===${NC}"
echo -e "Execution Role ARN: ${EXECUTION_ROLE_ARN}"
echo -e "Task Role ARN: ${TASK_ROLE_ARN}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update your task definition with these role ARNs"
echo "2. Run: ./deployment/update-task-definition.sh"