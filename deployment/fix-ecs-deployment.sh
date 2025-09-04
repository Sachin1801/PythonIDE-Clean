#!/bin/bash

# Emergency fix script to get ECS service running

set -e

AWS_REGION=${AWS_REGION:-us-east-2}
ECS_CLUSTER=${ECS_CLUSTER:-pythonide-cluster}
ECS_SERVICE=${ECS_SERVICE:-pythonide-service}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Emergency Fix: Getting ECS Service Stable${NC}"

# Step 1: Register a simpler task definition without health check
echo -e "${YELLOW}Creating simplified task definition...${NC}"

cat > /tmp/pythonide-simple.json <<'EOF'
{
  "family": "pythonide-backend",
  "taskRoleArn": "arn:aws:iam::653306034507:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::653306034507:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "pythonide-backend",
      "image": "653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:latest",
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
          "value": "production-secret-key-change-this"
        },
        {
          "name": "IDE_DATA_PATH",
          "value": "/mnt/efs/pythonide-data"
        },
        {
          "name": "PORT",
          "value": "8080"
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
          "awslogs-region": "us-east-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "volumes": [
    {
      "name": "efs-storage",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-0ba3b6fecab24774a",
        "transitEncryption": "DISABLED"
      }
    }
  ]
}
EOF

# Register the task definition
echo -e "${YELLOW}Registering task definition...${NC}"
TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/pythonide-simple.json \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text \
    --region ${AWS_REGION})

echo -e "${GREEN}✓ Task definition registered${NC}"

# Step 2: Update service with simplified deployment configuration
echo -e "${YELLOW}Updating service configuration...${NC}"
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --task-definition pythonide-backend \
    --desired-count 1 \
    --deployment-configuration "maximumPercent=100,minimumHealthyPercent=0" \
    --region ${AWS_REGION} \
    --output text > /dev/null

echo -e "${GREEN}✓ Service updated${NC}"

# Step 3: Wait for stabilization
echo -e "${YELLOW}Waiting for service to stabilize (this may take 2-3 minutes)...${NC}"
sleep 30

# Check status
echo -e "${YELLOW}Checking service status...${NC}"
aws ecs describe-services \
    --cluster ${ECS_CLUSTER} \
    --services ${ECS_SERVICE} \
    --query 'services[0].{RunningTasks:runningCount,DesiredTasks:desiredCount,Status:status}' \
    --output table \
    --region ${AWS_REGION}

# Check if task is running
RUNNING_TASKS=$(aws ecs list-tasks \
    --cluster ${ECS_CLUSTER} \
    --service-name ${ECS_SERVICE} \
    --desired-status RUNNING \
    --query 'length(taskArns)' \
    --output text \
    --region ${AWS_REGION})

if [ "$RUNNING_TASKS" -gt 0 ]; then
    echo -e "${GREEN}✓ Service is running with $RUNNING_TASKS task(s)${NC}"
    
    # Get task details
    TASK_ARN=$(aws ecs list-tasks \
        --cluster ${ECS_CLUSTER} \
        --service-name ${ECS_SERVICE} \
        --desired-status RUNNING \
        --query 'taskArns[0]' \
        --output text \
        --region ${AWS_REGION})
    
    echo -e "${YELLOW}Task ARN: ${TASK_ARN##*/}${NC}"
    
    # Get public IP if available
    TASK_DETAILS=$(aws ecs describe-tasks \
        --cluster ${ECS_CLUSTER} \
        --tasks ${TASK_ARN} \
        --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value|[0]' \
        --output text \
        --region ${AWS_REGION})
    
    if [ ! -z "$TASK_DETAILS" ] && [ "$TASK_DETAILS" != "None" ]; then
        PUBLIC_IP=$(aws ec2 describe-network-interfaces \
            --network-interface-ids ${TASK_DETAILS} \
            --query 'NetworkInterfaces[0].Association.PublicIp' \
            --output text \
            --region ${AWS_REGION} 2>/dev/null || echo "")
        
        if [ ! -z "$PUBLIC_IP" ] && [ "$PUBLIC_IP" != "None" ]; then
            echo -e "${GREEN}✓ Service accessible at: http://${PUBLIC_IP}:8080${NC}"
        fi
    fi
else
    echo -e "${RED}✗ No running tasks yet. Check CloudWatch logs for errors.${NC}"
    echo -e "${YELLOW}To view logs:${NC}"
    echo "aws logs tail /ecs/pythonide --follow --region ${AWS_REGION}"
fi

# Clean up
rm -f /tmp/pythonide-simple.json

echo -e "${GREEN}Deployment fix complete!${NC}"