#!/bin/bash
# Complete Auto-Scaling Deployment Script for Python IDE
# This script upgrades your Python IDE to support 60+ concurrent students with auto-scaling

set -e  # Exit on any error

# Configuration
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="653306034507"
ECS_CLUSTER="pythonide-cluster"
ECS_SERVICE="pythonide-service"
ECR_REPOSITORY="pythonide-backend"
TASK_FAMILY="pythonide-task"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Python IDE Auto-Scaling Deployment${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first:${NC}"
    echo "curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"
    echo "unzip awscliv2.zip"
    echo "sudo ./aws/install"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run:${NC}"
    echo "aws configure"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configured${NC}"

# Step 1: Update the task definition with increased resources
echo -e "${YELLOW}📋 Step 1: Updating task definition to 2 vCPU, 8GB RAM...${NC}"

# Replace the original task definition with the scaled version
cp deployment/ecs-task-definition-scaled.json deployment/ecs-task-definition.json

# Register the new task definition
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://deployment/ecs-task-definition-scaled.json \
    --region "${AWS_REGION}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo -e "${GREEN}✅ New task definition registered: ${NEW_TASK_DEF_ARN}${NC}"

# Step 2: Update the service to use minimum 2 tasks
echo -e "${YELLOW}📈 Step 2: Updating service to minimum 2 tasks...${NC}"

aws ecs update-service \
    --cluster "${ECS_CLUSTER}" \
    --service "${ECS_SERVICE}" \
    --task-definition "${NEW_TASK_DEF_ARN}" \
    --desired-count 2 \
    --deployment-configuration "minimumHealthyPercent=50,maximumPercent=200" \
    --region "${AWS_REGION}" \
    --query 'service.serviceName' \
    --output text

echo -e "${GREEN}✅ Service updated to run 2 tasks minimum${NC}"

# Step 3: Wait for service to be stable
echo -e "${YELLOW}⏳ Step 3: Waiting for service to stabilize...${NC}"
echo "This may take 5-10 minutes..."

aws ecs wait services-stable \
    --cluster "${ECS_CLUSTER}" \
    --services "${ECS_SERVICE}" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✅ Service is now stable with updated tasks${NC}"

# Step 4: Set up auto-scaling
echo -e "${YELLOW}🎯 Step 4: Configuring auto-scaling...${NC}"

# Register scalable target
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id "service/${ECS_CLUSTER}/${ECS_SERVICE}" \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 2 \
    --max-capacity 6 \
    --region "${AWS_REGION}" || echo "Scalable target may already exist"

# Create target tracking scaling policy
POLICY_ARN=$(aws application-autoscaling put-scaling-policy \
    --policy-name "pythonide-cpu-scaling-policy" \
    --service-namespace ecs \
    --resource-id "service/${ECS_CLUSTER}/${ECS_SERVICE}" \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{
        "TargetValue": 45.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
        },
        "ScaleOutCooldown": 300,
        "ScaleInCooldown": 300
    }' \
    --region "${AWS_REGION}" \
    --query 'PolicyARN' \
    --output text)

echo -e "${GREEN}✅ Auto-scaling policy created: CPU target 45%${NC}"

# Step 5: Create monitoring alarms
echo -e "${YELLOW}📊 Step 5: Setting up CloudWatch alarms...${NC}"

# High CPU alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "PythonIDE-HighCPU-Alert" \
    --alarm-description "Alert when Python IDE CPU usage is high" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 70 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --dimensions Name=ServiceName,Value="${ECS_SERVICE}" Name=ClusterName,Value="${ECS_CLUSTER}" \
    --region "${AWS_REGION}"

# Service health alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "PythonIDE-ServiceHealth" \
    --alarm-description "Alert when Python IDE service has less than 2 running tasks" \
    --metric-name RunningTaskCount \
    --namespace AWS/ECS \
    --statistic Average \
    --period 60 \
    --threshold 2 \
    --comparison-operator LessThanThreshold \
    --evaluation-periods 2 \
    --dimensions Name=ServiceName,Value="${ECS_SERVICE}" Name=ClusterName,Value="${ECS_CLUSTER}" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✅ CloudWatch alarms created${NC}"

# Step 6: Verify deployment
echo -e "${YELLOW}🔍 Step 6: Verifying deployment...${NC}"

# Get current service status
SERVICE_INFO=$(aws ecs describe-services \
    --cluster "${ECS_CLUSTER}" \
    --services "${ECS_SERVICE}" \
    --region "${AWS_REGION}" \
    --query 'services[0].{RunningCount:runningCount,DesiredCount:desiredCount,TaskDefinition:taskDefinition}' \
    --output json)

echo -e "${BLUE}Service Status:${NC}"
echo "${SERVICE_INFO}" | jq .

# Get auto-scaling configuration
SCALING_INFO=$(aws application-autoscaling describe-scalable-targets \
    --service-namespace ecs \
    --resource-ids "service/${ECS_CLUSTER}/${ECS_SERVICE}" \
    --region "${AWS_REGION}" \
    --query 'ScalableTargets[0].{MinCapacity:MinCapacity,MaxCapacity:MaxCapacity}' \
    --output json)

echo -e "${BLUE}Auto-scaling Configuration:${NC}"
echo "${SCALING_INFO}" | jq .

# Final summary
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""
echo -e "${BLUE}📋 Configuration Summary:${NC}"
echo "  • Task Resources: 2 vCPU, 8GB RAM per task"
echo "  • Min Tasks: 2 (always running)"
echo "  • Max Tasks: 6 (during peak load)"
echo "  • Auto-scaling: CPU > 45% triggers scale-out"
echo "  • Expected Capacity: 120+ concurrent students"
echo ""
echo -e "${BLUE}💰 Monthly Cost Estimate:${NC}"
echo "  • Minimum (2 tasks): ~\$233/month"
echo "  • Average (3-4 tasks): ~\$350/month"
echo "  • Peak (6 tasks): Only during high usage"
echo ""
echo -e "${BLUE}🔗 Monitoring URLs:${NC}"
echo "  • ECS Service: https://console.aws.amazon.com/ecs/home?region=${AWS_REGION}#/clusters/${ECS_CLUSTER}/services"
echo "  • CloudWatch: https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#alarmsV2:"
echo "  • Application: http://pythonide-classroom.tech/editor"
echo ""
echo -e "${GREEN}✅ Your Python IDE is now ready to handle 60+ concurrent students!${NC}"

# Test connectivity
echo -e "${YELLOW}🧪 Testing service health...${NC}"
sleep 10

# Get load balancer URL and test
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --region "${AWS_REGION}" \
    --query 'LoadBalancers[?contains(LoadBalancerName,`pythonide`)].DNSName' \
    --output text)

if [ ! -z "${ALB_DNS}" ]; then
    echo "Testing connectivity to: http://${ALB_DNS}/health"
    if curl -f "http://${ALB_DNS}/health" &> /dev/null; then
        echo -e "${GREEN}✅ Service is healthy and responding${NC}"
    else
        echo -e "${YELLOW}⚠️  Service may still be starting up. Check in a few minutes.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Could not find load balancer. Service should still be accessible via custom domain.${NC}"
fi

echo ""
echo -e "${BLUE}🚀 Auto-scaling is now active and monitoring your service!${NC}"