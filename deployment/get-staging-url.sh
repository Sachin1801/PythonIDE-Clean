#!/bin/bash
# Quick script to find the current staging environment URL
# ECS tasks with public IPs get new IPs on every redeployment

set -e

echo "🔍 Finding staging environment URL..."
echo ""

# Use default AWS credentials (no profile needed)
REGION="us-east-2"
CLUSTER="pythonide-cluster"
SERVICE="pythonide-staging-service"

# Get the running task ARN
echo "📋 Getting task ARN..."
TASK_ARN=$(aws ecs list-tasks \
    --cluster "$CLUSTER" \
    --service-name "$SERVICE" \
    --region "$REGION" \
    --query 'taskArns[0]' \
    --output text)

if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" = "None" ]; then
    echo "❌ No running tasks found for staging service"
    exit 1
fi

TASK_ID=$(echo "$TASK_ARN" | awk -F'/' '{print $NF}')
echo "✅ Task ID: $TASK_ID"
echo ""

# Get network interface ID from task
echo "🌐 Getting network interface..."
ENI=$(aws ecs describe-tasks \
    --cluster "$CLUSTER" \
    --tasks "$TASK_ID" \
    --region "$REGION" \
    --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
    --output text)

if [ -z "$ENI" ] || [ "$ENI" = "None" ]; then
    echo "❌ Could not find network interface for task"
    exit 1
fi

echo "✅ Network Interface: $ENI"
echo ""

# Get public IP from network interface
echo "📍 Getting public IP..."
PUBLIC_IP=$(aws ec2 describe-network-interfaces \
    --network-interface-ids "$ENI" \
    --region "$REGION" \
    --query 'NetworkInterfaces[0].Association.PublicIp' \
    --output text)

if [ -z "$PUBLIC_IP" ] || [ "$PUBLIC_IP" = "None" ]; then
    echo "❌ Task does not have a public IP"
    exit 1
fi

echo "✅ Public IP: $PUBLIC_IP"
echo ""
echo "================================================"
echo "🎯 STAGING URL:"
echo "   http://$PUBLIC_IP:8080"
echo "================================================"
echo ""
echo "📝 Credentials:"
echo "   Admin:   sa9082 / Admin@sa9082"
echo "   Student: test_1 / student@test_1"
echo ""
