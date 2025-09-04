#!/bin/bash

# Script to update and register the ECS task definition with correct values

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-2}
ECS_CLUSTER=${ECS_CLUSTER:-pythonide-cluster}
ECS_SERVICE=${ECS_SERVICE:-pythonide-service}
ECR_REPOSITORY=${ECR_REPOSITORY:-pythonide-backend}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Updating ECS Task Definition...${NC}"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "AWS Account ID: ${AWS_ACCOUNT_ID}"

# Get IAM Roles
echo -e "${YELLOW}Finding IAM roles...${NC}"
EXECUTION_ROLE_ARN=$(aws iam get-role --role-name ecsTaskExecutionRole --query 'Role.Arn' --output text 2>/dev/null || echo "")
TASK_ROLE_ARN=$(aws iam get-role --role-name ecsTaskRole --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$EXECUTION_ROLE_ARN" ]; then
    echo -e "${RED}Error: ecsTaskExecutionRole not found!${NC}"
    echo "Run ./deployment/setup-ecs-roles.sh first"
    exit 1
fi

if [ -z "$TASK_ROLE_ARN" ]; then
    echo -e "${YELLOW}Warning: ecsTaskRole not found. Creating it now...${NC}"
    ./deployment/setup-ecs-roles.sh
    TASK_ROLE_ARN=$(aws iam get-role --role-name ecsTaskRole --query 'Role.Arn' --output text)
fi

# Get RDS endpoint
echo -e "${YELLOW}Finding RDS instance...${NC}"
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --query 'DBInstances[?DBName==`pythonide`].Endpoint.Address | [0]' \
    --output text \
    --region ${AWS_REGION} 2>/dev/null || echo "")

if [ -z "$RDS_ENDPOINT" ] || [ "$RDS_ENDPOINT" = "None" ]; then
    echo -e "${YELLOW}RDS instance not found. Using placeholder.${NC}"
    RDS_ENDPOINT="your-rds-endpoint.rds.amazonaws.com"
    DATABASE_URL="postgresql://pythonide:your-password@${RDS_ENDPOINT}:5432/pythonide"
else
    echo -e "${GREEN}Found RDS: ${RDS_ENDPOINT}${NC}"
    echo -e "${YELLOW}Enter the database password:${NC}"
    read -s DB_PASSWORD
    DATABASE_URL="postgresql://pythonide:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/pythonide"
fi

# Get EFS filesystem ID
echo -e "${YELLOW}Finding EFS filesystem...${NC}"
EFS_ID=$(aws efs describe-file-systems \
    --query 'FileSystems[?Name==`pythonide-efs`].FileSystemId | [0]' \
    --output text \
    --region ${AWS_REGION} 2>/dev/null || echo "")

if [ -z "$EFS_ID" ] || [ "$EFS_ID" = "None" ]; then
    # Try without name filter
    EFS_ID=$(aws efs describe-file-systems \
        --query 'FileSystems[0].FileSystemId' \
        --output text \
        --region ${AWS_REGION} 2>/dev/null || echo "")
fi

if [ -z "$EFS_ID" ] || [ "$EFS_ID" = "None" ]; then
    echo -e "${RED}Error: No EFS filesystem found!${NC}"
    echo "Please create an EFS filesystem first or specify the EFS_ID"
    echo "Example: EFS_ID=fs-12345678 ./deployment/update-task-definition.sh"
    exit 1
fi

echo -e "${GREEN}Found EFS: ${EFS_ID}${NC}"

# Get or generate secret key
if [ -z "$IDE_SECRET_KEY" ]; then
    echo -e "${YELLOW}Generating IDE secret key...${NC}"
    IDE_SECRET_KEY=$(openssl rand -hex 32)
fi

# Create updated task definition
echo -e "${YELLOW}Creating task definition...${NC}"
cat > /tmp/pythonide-task-definition.json <<EOF
{
  "family": "pythonide-task",
  "taskRoleArn": "${TASK_ROLE_ARN}",
  "executionRoleArn": "${EXECUTION_ROLE_ARN}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "pythonide-backend",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "${DATABASE_URL}"
        },
        {
          "name": "IDE_SECRET_KEY",
          "value": "${IDE_SECRET_KEY}"
        },
        {
          "name": "IDE_DATA_PATH",
          "value": "/mnt/efs/pythonide-data"
        },
        {
          "name": "PORT",
          "value": "8080"
        },
        {
          "name": "MAX_CONCURRENT_EXECUTIONS",
          "value": "60"
        },
        {
          "name": "EXECUTION_TIMEOUT",
          "value": "30"
        },
        {
          "name": "MEMORY_LIMIT_MB",
          "value": "128"
        }
      ],
      "mountPoints": [
        {
          "sourceVolume": "efs-storage",
          "containerPath": "/mnt/efs"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pythonide",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "linuxParameters": {
        "initProcessEnabled": true
      }
    }
  ],
  "volumes": [
    {
      "name": "efs-storage",
      "efsVolumeConfiguration": {
        "fileSystemId": "${EFS_ID}",
        "transitEncryption": "ENABLED",
        "authorizationConfig": {
          "iam": "DISABLED"
        }
      }
    }
  ]
}
EOF

# Create CloudWatch log group if it doesn't exist
echo -e "${YELLOW}Creating CloudWatch log group...${NC}"
aws logs create-log-group --log-group-name /ecs/pythonide --region ${AWS_REGION} 2>/dev/null || true

# Register the task definition
echo -e "${YELLOW}Registering task definition...${NC}"
TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/pythonide-task-definition.json \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text \
    --region ${AWS_REGION})

echo -e "${GREEN}✓ Task definition registered successfully!${NC}"
echo -e "Task Definition ARN: ${TASK_DEF_ARN}"

# Update the service to use the new task definition
read -p "Do you want to update the ECS service with this task definition? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Updating ECS service...${NC}"
    aws ecs update-service \
        --cluster ${ECS_CLUSTER} \
        --service ${ECS_SERVICE} \
        --task-definition pythonide-task \
        --region ${AWS_REGION}
    
    echo -e "${GREEN}✓ Service updated!${NC}"
    echo -e "Monitor deployment: aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE}"
fi

# Save configuration for reference
echo -e "${YELLOW}Saving configuration...${NC}"
cat > deployment/last-deployment-config.txt <<EOF
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
AWS_REGION=${AWS_REGION}
ECS_CLUSTER=${ECS_CLUSTER}
ECS_SERVICE=${ECS_SERVICE}
EFS_ID=${EFS_ID}
RDS_ENDPOINT=${RDS_ENDPOINT}
IDE_SECRET_KEY=${IDE_SECRET_KEY}
TASK_ROLE_ARN=${TASK_ROLE_ARN}
EXECUTION_ROLE_ARN=${EXECUTION_ROLE_ARN}
EOF

echo -e "${GREEN}Configuration saved to deployment/last-deployment-config.txt${NC}"
echo -e "${YELLOW}Keep this file secure - it contains sensitive information!${NC}"

# Clean up
rm -f /tmp/pythonide-task-definition.json