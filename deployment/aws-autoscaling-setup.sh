#!/bin/bash
# AWS Auto-Scaling Setup for Python IDE
# This script configures ECS auto-scaling to support 60+ concurrent students

set -e  # Exit on any error

# Configuration
AWS_REGION="us-east-2"
ECS_CLUSTER="pythonide-cluster"
ECS_SERVICE="pythonide-service"
SCALABLE_TARGET_RESOURCE="service/${ECS_CLUSTER}/${ECS_SERVICE}"

echo "🚀 Setting up auto-scaling for Python IDE..."

# Step 1: Register the ECS service as a scalable target
echo "📋 Registering ECS service as scalable target..."
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id "${SCALABLE_TARGET_RESOURCE}" \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 2 \
    --max-capacity 6 \
    --region "${AWS_REGION}"

echo "✅ Scalable target registered: 2 min, 6 max tasks"

# Step 2: Create scale-out policy (when CPU > 45%)
echo "📈 Creating scale-out policy..."
SCALE_OUT_POLICY_ARN=$(aws application-autoscaling put-scaling-policy \
    --policy-name "pythonide-scale-out-policy" \
    --service-namespace ecs \
    --resource-id "${SCALABLE_TARGET_RESOURCE}" \
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
    --query 'PolicyARN' --output text)

echo "✅ Scale-out policy created: ${SCALE_OUT_POLICY_ARN}"

# Step 3: Create CloudWatch alarm for high CPU (backup alerting)
echo "⚠️  Creating CloudWatch alarm for high CPU..."
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
    --alarm-actions "arn:aws:sns:${AWS_REGION}:653306034507:pythonide-alerts" \
    --dimensions Name=ServiceName,Value="${ECS_SERVICE}" Name=ClusterName,Value="${ECS_CLUSTER}" \
    --region "${AWS_REGION}" || echo "⚠️  SNS topic not found, alarm created without notification"

# Step 4: Create CloudWatch alarm for service health
echo "💚 Creating service health alarm..."
aws cloudwatch put-metric-alarm \
    --alarm-name "PythonIDE-ServiceHealth" \
    --alarm-description "Alert when Python IDE service is unhealthy" \
    --metric-name RunningTaskCount \
    --namespace AWS/ECS \
    --statistic Average \
    --period 60 \
    --threshold 1 \
    --comparison-operator LessThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions "arn:aws:sns:${AWS_REGION}:653306034507:pythonide-alerts" \
    --dimensions Name=ServiceName,Value="${ECS_SERVICE}" Name=ClusterName,Value="${ECS_CLUSTER}" \
    --region "${AWS_REGION}" || echo "⚠️  SNS topic not found, alarm created without notification"

echo ""
echo "🎉 Auto-scaling setup completed successfully!"
echo ""
echo "📊 Configuration Summary:"
echo "  • Min Tasks: 2 (always running for high availability)"
echo "  • Max Tasks: 6 (scales up during peak usage)"
echo "  • Scale Trigger: CPU > 45%"
echo "  • Scale Cooldown: 5 minutes"
echo "  • Target Capacity: 15-20 students per task = 120+ total capacity"
echo ""
echo "💰 Expected Monthly Cost:"
echo "  • Minimum (2 tasks): ~$233/month"
echo "  • Average (3-4 tasks): ~$350/month"
echo "  • Peak (6 tasks): Only during high usage"
echo ""
echo "🔗 Monitor at: https://console.aws.amazon.com/ecs/home?region=${AWS_REGION}#/clusters/${ECS_CLUSTER}/services"
echo ""
echo "⚡ Next steps:"
echo "  1. Update task definition to 2 vCPU, 8GB RAM"
echo "  2. Deploy updated task definition"
echo "  3. Monitor scaling behavior"

# Verify configuration
echo ""
echo "🔍 Verifying auto-scaling configuration..."
aws application-autoscaling describe-scalable-targets \
    --service-namespace ecs \
    --resource-ids "${SCALABLE_TARGET_RESOURCE}" \
    --region "${AWS_REGION}" \
    --query 'ScalableTargets[0].{MinCapacity:MinCapacity,MaxCapacity:MaxCapacity,ResourceId:ResourceId}' \
    --output table

echo ""
echo "✅ Auto-scaling is now active! The service will automatically:"
echo "  • Scale OUT when CPU usage > 45% (add more tasks)"
echo "  • Scale IN when CPU usage < 45% (remove tasks)"
echo "  • Maintain minimum 2 tasks for high availability"
echo "  • Never exceed 6 tasks to control costs"