#!/bin/bash

# EXAM SCALING QUICK COMMANDS
# Use these commands to scale the exam service for optimal performance
# Region: us-east-2
# Cluster: pythonide-cluster
# Service: pythonide-exam-task-service

echo "=== PYTHONIDE EXAM SCALING COMMANDS ==="
echo ""

# ============================================================
# OPTION 1: SCALE TO 2 TASKS (RECOMMENDED - 5 MINUTES)
# ============================================================
echo "[OPTION 1] Scale to 2 Tasks (doubles capacity)"
echo "Command:"
echo "aws ecs update-service \\"
echo "  --cluster pythonide-cluster \\"
echo "  --service pythonide-exam-task-service \\"
echo "  --desired-count 2 \\"
echo "  --region us-east-2"
echo ""
echo "Copy and paste the above to scale to 2 tasks"
echo ""

# ============================================================
# OPTION 2: CHECK CURRENT STATUS
# ============================================================
echo "[CHECK] Current Service Status"
echo "Command:"
echo "aws ecs describe-services \\"
echo "  --cluster pythonide-cluster \\"
echo "  --services pythonide-exam-task-service \\"
echo "  --region us-east-2 | jq '.services[0] | {desiredCount, runningCount, taskDefinition}'"
echo ""

# ============================================================
# OPTION 3: VERIFY LOAD BALANCER HEALTH
# ============================================================
echo "[VERIFY] Load Balancer Health Checks"
echo "Command:"
echo "aws elbv2 describe-target-health \\"
echo "  --target-group-arn arn:aws:elasticloadbalancing:us-east-2:653306034507:targetgroup/pythonide-exam-tg/e058f73271f1595b \\"
echo "  --region us-east-2 | jq '.TargetHealthDescriptions[] | {Target: .Target.Id, State: .TargetHealth.State}'"
echo ""

# ============================================================
# OPTION 4: CHECK DATABASE CONNECTION POOL
# ============================================================
echo "[VERIFY] Database Connection Status"
echo "Command:"
echo "psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com \\"
echo "  -U pythonide_admin \\"
echo "  -d pythonide_exam \\"
echo "  -c \"SELECT datname, count(*) as connections FROM pg_stat_activity GROUP BY datname;\""
echo ""
echo "You'll be prompted for password: Sachinadlakha9082"
echo ""

# ============================================================
# OPTION 5: SCALE BACK TO 1 TASK (AFTER EXAM)
# ============================================================
echo "[POST-EXAM] Scale Back to 1 Task (cost savings)"
echo "Command:"
echo "aws ecs update-service \\"
echo "  --cluster pythonide-cluster \\"
echo "  --service pythonide-exam-task-service \\"
echo "  --desired-count 1 \\"
echo "  --region us-east-2"
echo ""

# ============================================================
# OPTION 6: VIEW RECENT LOGS
# ============================================================
echo "[DEBUG] View Recent Logs"
echo "Command:"
echo "aws logs tail /aws/ecs/pythonide-exam --follow --region us-east-2"
echo ""

# ============================================================
# OPTION 7: FORCE NEW DEPLOYMENT (IF IMAGE WAS UPDATED)
# ============================================================
echo "[DEPLOY] Force New Deployment of Latest Image"
echo "Command:"
echo "aws ecs update-service \\"
echo "  --cluster pythonide-cluster \\"
echo "  --service pythonide-exam-task-service \\"
echo "  --force-new-deployment \\"
echo "  --region us-east-2"
echo ""

echo "=== END OF COMMANDS ==="
