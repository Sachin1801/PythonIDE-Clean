#!/bin/bash

# Start Staging Environment

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Starting staging environment...${NC}"

aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-staging-service \
  --desired-count 1 \
  --region us-east-2 > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Service update initiated${NC}"
else
    echo -e "${RED}❌ Failed to start service. Check AWS CLI configuration.${NC}"
    exit 1
fi

echo -e "${YELLOW}⏳ Waiting for task to start (30 seconds)...${NC}"
sleep 30

echo -e "${YELLOW}📊 Getting task information...${NC}"

TASK_ARN=$(aws ecs list-tasks \
  --cluster pythonide-cluster \
  --service-name pythonide-staging-service \
  --region us-east-2 \
  --query 'taskArns[0]' \
  --output text 2>/dev/null)

if [ "$TASK_ARN" != "None" ] && [ -n "$TASK_ARN" ]; then
    echo -e "${GREEN}✅ Task running: $TASK_ARN${NC}"

    # Try to get public IP
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
            echo -e "${GREEN}✅ Staging URL: http://$TASK_IP:8080${NC}"
            echo ""
            echo "Test commands:"
            echo "  curl http://$TASK_IP:8080/health"
            echo "  ./simple_load_test.sh 20  # Change URL in script first"
        else
            echo -e "${YELLOW}⚠️ Could not get public IP. Check ECS console.${NC}"
        fi
    fi
else
    echo -e "${RED}❌ Task failed to start${NC}"
    echo "Check CloudWatch logs: /ecs/pythonide-staging"
    echo "Or AWS Console: ECS → pythonide-cluster → pythonide-staging-service"
fi

echo ""
echo -e "${YELLOW}💰 Cost: ~$0.04/hour while running${NC}"
echo -e "${YELLOW}Remember to stop when done: ./deployment/stop-staging.sh${NC}"