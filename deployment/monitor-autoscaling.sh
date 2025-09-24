#!/bin/bash
# Auto-Scaling Monitoring Script for Python IDE
# This script checks the current status of auto-scaling and provides insights

set -e

# Configuration
AWS_REGION="us-east-2"
ECS_CLUSTER="pythonide-cluster"
ECS_SERVICE="pythonide-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📊 Python IDE Auto-Scaling Status${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    exit 1
fi

# 1. Current Service Status
echo -e "${YELLOW}🏃 Current Service Status:${NC}"
SERVICE_STATUS=$(aws ecs describe-services \
    --cluster "${ECS_CLUSTER}" \
    --services "${ECS_SERVICE}" \
    --region "${AWS_REGION}" \
    --query 'services[0].{Status:status,TaskDefinition:taskDefinition,RunningCount:runningCount,DesiredCount:desiredCount,PendingCount:pendingCount}' \
    --output json)

echo "${SERVICE_STATUS}" | jq .
echo ""

# 2. Task Resource Configuration
echo -e "${YELLOW}💪 Task Resources:${NC}"
TASK_DEF_ARN=$(echo "${SERVICE_STATUS}" | jq -r .TaskDefinition)
TASK_RESOURCES=$(aws ecs describe-task-definition \
    --task-definition "${TASK_DEF_ARN}" \
    --region "${AWS_REGION}" \
    --query 'taskDefinition.{CPU:cpu,Memory:memory,Family:family,Revision:revision}' \
    --output json)

echo "${TASK_RESOURCES}" | jq .

# Calculate estimated capacity
CPU=$(echo "${TASK_RESOURCES}" | jq -r .CPU)
MEMORY=$(echo "${TASK_RESOURCES}" | jq -r .Memory)
RUNNING_TASKS=$(echo "${SERVICE_STATUS}" | jq -r .RunningCount)

if [[ "${CPU}" == "2048" && "${MEMORY}" == "8192" ]]; then
    ESTIMATED_CAPACITY=$((RUNNING_TASKS * 20))
    echo -e "${GREEN}✅ Optimal resources: ${CPU} CPU, ${MEMORY}MB RAM${NC}"
    echo -e "${GREEN}📊 Estimated capacity: ~${ESTIMATED_CAPACITY} concurrent students${NC}"
elif [[ "${CPU}" == "1024" && "${MEMORY}" == "4096" ]]; then
    ESTIMATED_CAPACITY=$((RUNNING_TASKS * 10))
    echo -e "${YELLOW}⚠️  Legacy resources: ${CPU} CPU, ${MEMORY}MB RAM${NC}"
    echo -e "${YELLOW}📊 Estimated capacity: ~${ESTIMATED_CAPACITY} concurrent students${NC}"
    echo -e "${YELLOW}💡 Consider upgrading to 2048 CPU, 8192 Memory for better performance${NC}"
else
    echo -e "${RED}❓ Unknown resource configuration${NC}"
fi
echo ""

# 3. Auto-Scaling Configuration
echo -e "${YELLOW}🎯 Auto-Scaling Configuration:${NC}"
SCALING_TARGET=$(aws application-autoscaling describe-scalable-targets \
    --service-namespace ecs \
    --resource-ids "service/${ECS_CLUSTER}/${ECS_SERVICE}" \
    --region "${AWS_REGION}" \
    --query 'ScalableTargets[0].{MinCapacity:MinCapacity,MaxCapacity:MaxCapacity,ResourceId:ResourceId}' \
    --output json 2>/dev/null) || SCALING_TARGET=""

if [[ "${SCALING_TARGET}" != "" && "${SCALING_TARGET}" != "null" ]]; then
    echo "${SCALING_TARGET}" | jq .
    
    MIN_CAP=$(echo "${SCALING_TARGET}" | jq -r .MinCapacity)
    MAX_CAP=$(echo "${SCALING_TARGET}" | jq -r .MaxCapacity)
    
    if [[ "${MIN_CAP}" == "2" && "${MAX_CAP}" == "6" ]]; then
        echo -e "${GREEN}✅ Optimal auto-scaling: ${MIN_CAP} min, ${MAX_CAP} max tasks${NC}"
    else
        echo -e "${YELLOW}⚠️  Auto-scaling: ${MIN_CAP} min, ${MAX_CAP} max tasks${NC}"
    fi
else
    echo -e "${RED}❌ Auto-scaling not configured!${NC}"
    echo -e "${YELLOW}💡 Run: ./deployment/aws-autoscaling-setup.sh${NC}"
fi
echo ""

# 4. Auto-Scaling Policies
echo -e "${YELLOW}📈 Scaling Policies:${NC}"
SCALING_POLICIES=$(aws application-autoscaling describe-scaling-policies \
    --service-namespace ecs \
    --resource-id "service/${ECS_CLUSTER}/${ECS_SERVICE}" \
    --region "${AWS_REGION}" \
    --query 'ScalingPolicies[0].{PolicyName:PolicyName,PolicyType:PolicyType}' \
    --output json 2>/dev/null) || SCALING_POLICIES=""

if [[ "${SCALING_POLICIES}" != "" && "${SCALING_POLICIES}" != "null" ]]; then
    echo "${SCALING_POLICIES}" | jq .
    echo -e "${GREEN}✅ CPU-based scaling policy active${NC}"
else
    echo -e "${RED}❌ No scaling policies found${NC}"
fi
echo ""

# 5. Current CPU Utilization
echo -e "${YELLOW}📊 Recent CPU Utilization (last 1 hour):${NC}"
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%S)
START_TIME=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)

CPU_METRICS=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value="${ECS_SERVICE}" Name=ClusterName,Value="${ECS_CLUSTER}" \
    --start-time "${START_TIME}" \
    --end-time "${END_TIME}" \
    --period 300 \
    --statistics Average \
    --region "${AWS_REGION}" \
    --query 'Datapoints | sort_by(@, &Timestamp) | [-12:]' \
    --output json 2>/dev/null) || CPU_METRICS=""

if [[ "${CPU_METRICS}" != "" && "${CPU_METRICS}" != "[]" ]]; then
    echo "Recent CPU usage:"
    echo "${CPU_METRICS}" | jq -r '.[] | "\(.Timestamp): \(.Average | round)%"'
    
    # Get latest CPU usage
    LATEST_CPU=$(echo "${CPU_METRICS}" | jq -r '.[-1].Average // 0')
    LATEST_CPU_INT=$(echo "${LATEST_CPU}" | cut -d. -f1)
    
    if (( LATEST_CPU_INT > 50 )); then
        echo -e "${RED}🔥 High CPU: ${LATEST_CPU_INT}% (may trigger scale-out)${NC}"
    elif (( LATEST_CPU_INT > 30 )); then
        echo -e "${YELLOW}⚠️  Moderate CPU: ${LATEST_CPU_INT}%${NC}"
    else
        echo -e "${GREEN}✅ Normal CPU: ${LATEST_CPU_INT}%${NC}"
    fi
else
    echo -e "${YELLOW}📊 No recent CPU metrics available${NC}"
fi
echo ""

# 6. CloudWatch Alarms
echo -e "${YELLOW}🚨 CloudWatch Alarms:${NC}"
ALARMS=$(aws cloudwatch describe-alarms \
    --alarm-names "PythonIDE-HighCPU-Alert" "PythonIDE-ServiceHealth" \
    --region "${AWS_REGION}" \
    --query 'MetricAlarms[].{AlarmName:AlarmName,StateValue:StateValue,StateReason:StateReason}' \
    --output json 2>/dev/null) || ALARMS=""

if [[ "${ALARMS}" != "" && "${ALARMS}" != "[]" ]]; then
    echo "${ALARMS}" | jq .
else
    echo -e "${YELLOW}⚠️  No CloudWatch alarms found${NC}"
fi
echo ""

# 7. Cost Estimation
if [[ "${RUNNING_TASKS}" ]]; then
    if [[ "${CPU}" == "2048" && "${MEMORY}" == "8192" ]]; then
        COST_PER_TASK=88.5
        CURRENT_COST=$(echo "scale=2; ${RUNNING_TASKS} * ${COST_PER_TASK}" | bc)
        echo -e "${BLUE}💰 Current Monthly Cost Estimate: \$${CURRENT_COST}${NC}"
        echo -e "${BLUE}   (${RUNNING_TASKS} tasks × \$${COST_PER_TASK}/task/month)${NC}"
        
        if [[ "${SCALING_TARGET}" != "" && "${SCALING_TARGET}" != "null" ]]; then
            MIN_COST=$(echo "scale=2; ${MIN_CAP} * ${COST_PER_TASK}" | bc)
            MAX_COST=$(echo "scale=2; ${MAX_CAP} * ${COST_PER_TASK}" | bc)
            echo -e "${BLUE}   Range: \$${MIN_COST} (min) to \$${MAX_COST} (max)${NC}"
        fi
    fi
fi
echo ""

# 8. Quick Health Check
echo -e "${YELLOW}🏥 Service Health Check:${NC}"
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --region "${AWS_REGION}" \
    --query 'LoadBalancers[?contains(LoadBalancerName,`pythonide`)].DNSName' \
    --output text 2>/dev/null) || ALB_DNS=""

if [[ "${ALB_DNS}" ]]; then
    if curl -f -m 10 "http://${ALB_DNS}/health" &> /dev/null; then
        echo -e "${GREEN}✅ Load balancer health check: PASSED${NC}"
    else
        echo -e "${RED}❌ Load balancer health check: FAILED${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Could not find load balancer${NC}"
fi

echo ""
echo -e "${BLUE}🔗 Useful Links:${NC}"
echo "  • ECS Console: https://console.aws.amazon.com/ecs/home?region=${AWS_REGION}#/clusters/${ECS_CLUSTER}/services"
echo "  • CloudWatch: https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#alarmsV2:"
echo "  • Application: http://pythonide-classroom.tech/editor"
echo ""

# Overall status summary
if [[ "${SCALING_TARGET}" != "" && "${SCALING_TARGET}" != "null" ]] && [[ "${CPU}" == "2048" ]]; then
    echo -e "${GREEN}🎉 AUTO-SCALING STATUS: OPTIMAL${NC}"
    echo -e "${GREEN}   Your Python IDE is ready for 60+ concurrent students!${NC}"
elif [[ "${SCALING_TARGET}" != "" && "${SCALING_TARGET}" != "null" ]]; then
    echo -e "${YELLOW}⚠️  AUTO-SCALING STATUS: NEEDS ATTENTION${NC}"
    echo -e "${YELLOW}   Auto-scaling is configured but task resources may be low${NC}"
else
    echo -e "${RED}❌ AUTO-SCALING STATUS: NOT CONFIGURED${NC}"
    echo -e "${RED}   Run ./deployment/deploy-autoscaling.sh to enable auto-scaling${NC}"
fi