#!/bin/bash

# Quick fix script to register task definition with correct container name

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-2}
ECS_CLUSTER=${ECS_CLUSTER:-pythonide-cluster}
ECS_SERVICE=${ECS_SERVICE:-pythonide-service}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Quick Fix: Registering task definition with correct container name...${NC}"

# Get values from last deployment
if [ -f deployment/last-deployment-config.txt ]; then
    source deployment/last-deployment-config.txt
fi

# Get AWS Account ID if not set
if [ -z "$AWS_ACCOUNT_ID" ]; then
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
fi

# Register the corrected task definition
echo -e "${YELLOW}Registering corrected task definition...${NC}"

cat > /tmp/pythonide-task-fix.json <<EOF
{
  "family": "pythonide-backend",
  "taskRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "pythonide-backend",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/pythonide-backend:latest",
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
          "value": "postgresql://pythonide:postgres@pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432/pythonide"
        },
        {
          "name": "IDE_SECRET_KEY",
          "value": "${IDE_SECRET_KEY:-$(openssl rand -hex 32)}"
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
          "value": "60"
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
        "fileSystemId": "fs-0ba3b6fecab24774a",
        "transitEncryption": "ENABLED",
        "authorizationConfig": {
          "iam": "DISABLED"
        }
      }
    }
  ]
}
EOF

# Register it
TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/pythonide-task-fix.json \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text \
    --region ${AWS_REGION})

echo -e "${GREEN}✓ Task definition registered: ${TASK_DEF_ARN}${NC}"

# Update service
echo -e "${YELLOW}Updating ECS service...${NC}"
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --task-definition pythonide-backend \
    --deployment-configuration "maximumPercent=100,minimumHealthyPercent=0" \
    --region ${AWS_REGION}

echo -e "${GREEN}✓ Service updated!${NC}"
echo ""
echo -e "${YELLOW}Monitor deployment:${NC}"
echo "aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE} --region ${AWS_REGION}"

# Clean up
rm -f /tmp/pythonide-task-fix.json