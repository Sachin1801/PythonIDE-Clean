# 🚀 Manual Staging Setup Guide

**Use this if the automated script has AWS CLI issues**

---

## Prerequisites

- AWS Console access to account 653306034507
- Region: us-east-2
- Production cluster: pythonide-cluster

---

## Step 1: Create Staging RDS Database (10 mins)

### Via AWS Console:

1. Go to **RDS Console** → **Create database**
2. Choose:
   - Engine: **PostgreSQL 15.7**
   - Templates: **Free tier** (or Dev/Test)
   - DB instance identifier: `pythonide-staging-db`
   - Master username: `pythonide_admin`
   - Master password: Generate strong password (save it!)
   - DB instance class: **db.t4g.micro**
   - Storage: **20 GB gp2**
   - VPC: Same as production
   - Subnet group: Same as production
   - Security group: Same as production (pythonide-sg)
   - Database name: `pythonide`
   - Backup retention: **0 days** (to save costs)
   - Multi-AZ: **No**
   - Public access: **No**

3. Click **Create database**
4. Wait 8-10 minutes for it to become available
5. **Copy the endpoint** (e.g., `pythonide-staging-db.xxxxx.us-east-2.rds.amazonaws.com`)

### Save Database Password:

```bash
# On your local machine
mkdir -p deployment
echo "YOUR_GENERATED_PASSWORD" > deployment/staging-db-password.txt
chmod 600 deployment/staging-db-password.txt
```

---

## Step 2: Create Staging Task Definition (5 mins)

### Via AWS Console:

1. Go to **ECS Console** → **Task Definitions**
2. Select `pythonide-task` → **Create new revision**
3. Modify the following:
   - Task family: Change to `pythonide-staging-task`
   - Task CPU: `512` (0.5 vCPU)
   - Task memory: `1024` (1 GB)
   - Container environment variables:
     - `DATABASE_URL`: `postgresql://pythonide_admin:YOUR_PASSWORD@YOUR_ENDPOINT:5432/pythonide`
     - `ENVIRONMENT`: `staging`
     - `TORNADO_PROCESSES`: `1`
4. Click **Create**

### Alternative: Use JSON File

Download the production task definition, modify it, and upload:

1. Go to `pythonide-task` → **JSON** tab
2. Copy the JSON
3. Create file `deployment/staging-task-definition.json`:

```json
{
  "family": "pythonide-staging-task",
  "taskRoleArn": "arn:aws:iam::653306034507:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::653306034507:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
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
          "value": "postgresql://pythonide_admin:YOUR_PASSWORD@YOUR_ENDPOINT:5432/pythonide"
        },
        {
          "name": "IDE_SECRET_KEY",
          "value": "@ok#N2q0%!F2zGUuC^rYvtY2Op#hkEWsMtBRDsk@5Bq7D8x#Y18kajwIrozM0YE6"
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
          "name": "ENVIRONMENT",
          "value": "staging"
        },
        {
          "name": "TORNADO_PROCESSES",
          "value": "1"
        }
      ],
      "mountPoints": [
        {
          "sourceVolume": "pythonide-efs",
          "containerPath": "/mnt/efs"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pythonide-staging",
          "awslogs-region": "us-east-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8080/health || exit 1"
        ],
        "interval": 60,
        "timeout": 10,
        "retries": 5,
        "startPeriod": 120
      }
    }
  ],
  "volumes": [
    {
      "name": "pythonide-efs",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-0ba3b6fecab24774a",
        "transitEncryption": "ENABLED",
        "authorizationConfig": {
          "iam": "ENABLED"
        }
      }
    }
  ]
}
```

4. Upload via AWS Console or CLI

---

## Step 3: Create Staging ECS Service (5 mins)

### Via AWS Console:

1. Go to **ECS Console** → **Clusters** → `pythonide-cluster`
2. Click **Create** in the Services tab
3. Configure:
   - Launch type: **Fargate**
   - Task Definition: `pythonide-staging-task:1`
   - Service name: `pythonide-staging-service`
   - Number of tasks: **0** (start stopped)
   - Deployment type: Rolling update
   - VPC: Same as production
   - Subnets: Same as production (select all available)
   - Security groups: Same as production
   - Auto-assign public IP: **ENABLED**
   - Load balancer: **None** (for now, we'll test without ALB first)
4. Click **Create Service**

---

## Step 4: Create CloudWatch Log Group (2 mins)

### Via AWS Console:

1. Go to **CloudWatch Console** → **Log groups**
2. Click **Create log group**
3. Name: `/ecs/pythonide-staging`
4. Retention: 7 days
5. Click **Create**

---

## Step 5: Test Staging (10 mins)

### Start Staging:

**Via Console:**
1. Go to ECS → Clusters → pythonide-cluster → pythonide-staging-service
2. Click **Update**
3. Change **Number of tasks** to **1**
4. Click **Update Service**

**Via CLI (if working):**
```bash
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-staging-service \
  --desired-count 1 \
  --region us-east-2
```

### Check Task IP:

1. Go to **Tasks** tab
2. Click on the running task
3. Find **Public IP** under Network section
4. Copy the IP address

### Test Health Endpoint:

```bash
# Replace with your task's public IP
curl http://XX.XX.XX.XX:8080/health

# Should return:
# {"status": "healthy", "database": "connected", ...}
```

### Check Logs:

1. Go to CloudWatch → Log groups → `/ecs/pythonide-staging`
2. Find the latest log stream
3. Look for:
   - "Server listening on 0.0.0.0:8080"
   - "Database type: PostgreSQL"
   - Any errors

### Stop Staging:

**Via Console:**
1. Go to ECS → pythonide-staging-service
2. Click **Update**
3. Change **Number of tasks** to **0**
4. Click **Update Service**

---

## Step 6: Create Helper Scripts (5 mins)

Create these scripts on your local machine:

### `deployment/start-staging.sh`:

```bash
#!/bin/bash
echo "🚀 Starting staging environment..."
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-staging-service \
  --desired-count 1 \
  --region us-east-2

echo "⏳ Waiting for task to start..."
sleep 30

echo "📊 Getting task IP..."
TASK_ARN=$(aws ecs list-tasks \
  --cluster pythonide-cluster \
  --service-name pythonide-staging-service \
  --region us-east-2 \
  --query 'taskArns[0]' \
  --output text)

if [ "$TASK_ARN" != "None" ]; then
    TASK_IP=$(aws ecs describe-tasks \
      --cluster pythonide-cluster \
      --tasks $TASK_ARN \
      --region us-east-2 \
      --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
      --output text | xargs -I {} aws ec2 describe-network-interfaces \
      --network-interface-ids {} \
      --region us-east-2 \
      --query 'NetworkInterfaces[0].Association.PublicIp' \
      --output text)

    echo "✅ Staging running at: http://$TASK_IP:8080"
    echo "Test: curl http://$TASK_IP:8080/health"
else
    echo "❌ Task failed to start. Check CloudWatch logs."
fi
```

### `deployment/stop-staging.sh`:

```bash
#!/bin/bash
echo "🛑 Stopping staging environment..."
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-staging-service \
  --desired-count 0 \
  --region us-east-2

echo "✅ Staging stopped (0 tasks running)"
echo "💰 Cost: ~$0.00/hour while stopped"
```

### `deployment/staging-status.sh`:

```bash
#!/bin/bash
echo "📊 Staging Environment Status:"
echo "================================"

# Service status
aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-staging-service \
  --region us-east-2 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount}'

# RDS status
echo ""
echo "RDS Database:"
aws rds describe-db-instances \
  --db-instance-identifier pythonide-staging-db \
  --region us-east-2 \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Endpoint:Endpoint.Address}'
```

Make them executable:
```bash
chmod +x deployment/*.sh
```

---

## Estimated Costs

| Resource | Configuration | Cost/Month |
|----------|--------------|------------|
| **RDS db.t4g.micro** | Always running | $12-14 |
| **ECS Fargate** | 0.5 vCPU, 1GB | $0.04/hour |
| **ECS Fargate (stopped)** | 0 tasks | $0.00 |

**Total when stopped**: ~$12-14/month (just RDS)
**Total when testing (2 hrs/month)**: ~$12-14/month (minimal ECS cost)

---

## Cost Optimization: On-Demand RDS

If you want to save even more ($12/month → $2/month):

### Option: Delete RDS when not testing

**Before Testing:**
```bash
# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier pythonide-staging-db \
  --db-snapshot-identifier pythonide-staging-snapshot-latest \
  --db-instance-class db.t4g.micro
```

**After Testing:**
```bash
# Create snapshot
aws rds create-db-snapshot \
  --db-instance-identifier pythonide-staging-db \
  --db-snapshot-identifier pythonide-staging-snapshot-$(date +%Y%m%d)

# Delete instance
aws rds delete-db-instance \
  --db-instance-identifier pythonide-staging-db \
  --skip-final-snapshot
```

**Snapshot storage**: ~$2/month (20GB)

---

## Troubleshooting

### Issue: Task won't start

**Check:**
1. CloudWatch logs: `/ecs/pythonide-staging`
2. Database connectivity
3. Security groups allow port 5432 from ECS tasks

**Fix:**
```bash
# Test DB from production task
aws ecs execute-command \
  --cluster pythonide-cluster \
  --task [PRODUCTION_TASK_ARN] \
  --container pythonide-backend \
  --command "psql -h pythonide-staging-db.[...].rds.amazonaws.com -U pythonide_admin -d pythonide" \
  --interactive
```

### Issue: Can't connect to health endpoint

**Possible causes:**
1. Security group blocking port 8080
2. Task not started yet (check ECS console)
3. Wrong IP address

**Fix:**
- Check security group rules
- Wait 2-3 minutes after starting
- Verify task is in RUNNING state

---

## Next Steps After Setup

1. ✅ Test basic functionality
2. ✅ Run load test: `./simple_load_test.sh 20`
3. ✅ Test with right-sized config (1 vCPU, 2GB)
4. ✅ Stop staging when done testing
5. ✅ Move to production optimization

---

## Quick Reference

**Start staging**: `./deployment/start-staging.sh`
**Stop staging**: `./deployment/stop-staging.sh`
**Check status**: `./deployment/staging-status.sh`
**View logs**: CloudWatch → `/ecs/pythonide-staging`

**Cost while running**: ~$0.04/hour
**Cost while stopped**: ~$12-14/month (RDS only)