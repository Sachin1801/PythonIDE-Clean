#!/bin/bash

# Check Staging Environment Status

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📊 Staging Environment Status${NC}"
echo -e "${BLUE}========================================${NC}"

# Check ECS Service
echo -e "\n${YELLOW}ECS Service (pythonide-staging-service):${NC}"
SERVICE_INFO=$(aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-staging-service \
  --region us-east-2 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount}' \
  --output json 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$SERVICE_INFO" | jq -r 'to_entries | .[] | "  \(.key): \(.value)"'

    RUNNING=$(echo "$SERVICE_INFO" | jq -r '.Running')
    if [ "$RUNNING" -gt 0 ]; then
        echo -e "  ${GREEN}✅ Staging is RUNNING${NC}"

        # Get task details
        TASK_ARN=$(aws ecs list-tasks \
          --cluster pythonide-cluster \
          --service-name pythonide-staging-service \
          --region us-east-2 \
          --query 'taskArns[0]' \
          --output text 2>/dev/null)

        if [ -n "$TASK_ARN" ] && [ "$TASK_ARN" != "None" ]; then
            echo -e "\n${YELLOW}Task Details:${NC}"
            echo "  Task ARN: $TASK_ARN"

            # Get task IP
            ENI_ID=$(aws ecs describe-tasks \
              --cluster pythonide-cluster \
              --tasks $TASK_ARN \
              --region us-east-2 \
              --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
              --output text 2>/dev/null)

            if [ -n "$ENI_ID" ]; then
                TASK_IP=$(aws ec2 describe-network-interfaces \
                  --network-interface-ids $ENI_ID \
                  --region us-east-2 \
                  --query 'NetworkInterfaces[0].Association.PublicIp' \
                  --output text 2>/dev/null)

                if [ -n "$TASK_IP" ] && [ "$TASK_IP" != "None" ]; then
                    echo "  Public IP: $TASK_IP"
                    echo "  Health URL: http://$TASK_IP:8080/health"

                    # Test health endpoint
                    echo -e "\n${YELLOW}Health Check:${NC}"
                    HEALTH=$(curl -s -m 5 http://$TASK_IP:8080/health 2>/dev/null)
                    if [ $? -eq 0 ]; then
                        echo "  $HEALTH" | jq '.' 2>/dev/null || echo "  $HEALTH"
                    else
                        echo -e "  ${RED}❌ Health check failed${NC}"
                    fi
                fi
            fi
        fi
    else
        echo -e "  ${YELLOW}⚪ Staging is STOPPED${NC}"
    fi
else
    echo -e "  ${RED}❌ Could not retrieve service status${NC}"
fi

# Check RDS Database
echo -e "\n${YELLOW}RDS Database (pythonide-staging-db):${NC}"
RDS_INFO=$(aws rds describe-db-instances \
  --db-instance-identifier pythonide-staging-db \
  --region us-east-2 \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Endpoint:Endpoint.Address,Class:DBInstanceClass}' \
  --output json 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$RDS_INFO" | jq -r 'to_entries | .[] | "  \(.key): \(.value)"'

    RDS_STATUS=$(echo "$RDS_INFO" | jq -r '.Status')
    if [ "$RDS_STATUS" = "available" ]; then
        echo -e "  ${GREEN}✅ Database is AVAILABLE${NC}"
    else
        echo -e "  ${YELLOW}⚠️ Database status: $RDS_STATUS${NC}"
    fi
else
    echo -e "  ${RED}❌ Database not found or not accessible${NC}"
fi

# Cost estimate
echo -e "\n${BLUE}========================================${NC}"
echo -e "${YELLOW}💰 Current Hourly Cost Estimate:${NC}"
RUNNING_COST=0
RDS_COST=0.02  # ~$0.02/hour for db.t4g.micro

if [ "$RUNNING" -gt 0 ]; then
    RUNNING_COST=0.04  # ~$0.04/hour for 0.5 vCPU, 1GB
    echo "  ECS Fargate: ~\$0.04/hour (RUNNING)"
else
    echo "  ECS Fargate: \$0.00/hour (STOPPED)"
fi

echo "  RDS Database: ~\$0.02/hour (always running)"
echo ""
TOTAL_COST=$(echo "$RUNNING_COST + $RDS_COST" | bc)
echo -e "${GREEN}  Total: ~\$$TOTAL_COST/hour${NC}"

MONTHLY_COST=$(echo "$TOTAL_COST * 730" | bc)
echo -e "${YELLOW}  Monthly (if always running): ~\$$MONTHLY_COST${NC}"

echo -e "\n${BLUE}========================================${NC}"