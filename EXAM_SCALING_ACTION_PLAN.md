# Exam Scaling Action Plan - 1 Hour Before Exam

**Generated**: October 23, 2025
**Exam Start**: ~1 hour from now
**Students**: 34 enrolled students + 3 professors
**Current Bottleneck**: Single 1 vCPU task with NO auto-scaling

---

## CRITICAL FINDING: NO AUTO-SCALING CURRENTLY SET UP ⚠️

### Current Status:
- **Auto-scaling**: ❌ NOT CONFIGURED
- **Task Count**: 1 (fixed, will NOT increase under load)
- **CPU/Memory**: 1 vCPU / 2 GB (fixed, cannot scale)
- **Risk Level**: **HIGH** - Single point of failure with no failover

### What Happens If Load Spikes:
1. All 34+ students hit 100% CPU utilization
2. NO automatic task scaling occurs
3. NO capacity expansion
4. Students experience:
   - Slow code execution (>10 seconds per run)
   - Page timeouts
   - WebSocket disconnections
   - Frozen IDE

---

## IMMEDIATE ACTIONS FOR EXAM (Next 60 Minutes)

### OPTION A: Quick Fix - Scale to 2 Tasks Manually (RECOMMENDED - 5 Minutes)

**Why This Works:**
- Doubles processing capacity (1→2 vCPU)
- Distributes load across 2 containers
- Maintains data consistency (shared EFS, separate DB)
- Can be reverted quickly if issues arise

**Steps:**

```bash
# 1. Scale to 2 tasks NOW
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-exam-task-service \
  --desired-count 2 \
  --region us-east-2

# 2. Wait for both tasks to start (2-3 minutes)
# Monitor: AWS Console > ECS > pythonide-cluster > pythonide-exam-task-service
# Look for: Desired: 2, Running: 2

# 3. Verify health checks pass
aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-exam-task-service \
  --region us-east-2 | jq '.services[0].deployments'

# Expected output:
# - Two tasks with status "RUNNING"
# - Both passing health checks
# - DesiredCount: 2
# - RunningCount: 2
```

**Capacity After Scaling to 2 Tasks:**
| Metric | Single Task | 2 Tasks | Headroom |
|--------|-------------|---------|----------|
| Total vCPU | 1 | 2 | 100% extra |
| Total Memory | 2 GB | 4 GB | 100% extra |
| Per-Student Capacity | 29 MB/student | 59 MB/student | 2x better |
| Estimated CPU at 34 students | 60-70% | 30-35% | Safe ✓ |

---

### OPTION B: Increase CPU/Memory in Task Definition (5 Minutes)

**If you want higher baseline without adding tasks:**

```bash
# 1. Update task definition to 2 vCPU / 4 GB
aws ecs register-task-definition \
  --family pythonide-exam-task \
  --cpu 2048 \
  --memory 4096 \
  --container-definitions '[{
    "name": "pythonide-exam",
    "image": "653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-exam:latest",
    "cpu": 2048,
    "memory": 4096,
    "portMappings": [{"containerPort": 8080}],
    "environment": [
      {"name": "DATABASE_URL", "value": "postgresql://pythonide_admin:Sachinadlakha9082@pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432/pythonide_exam"},
      {"name": "IDE_DATA_PATH", "value": "/mnt/efs/pythonide-data-exam"},
      {"name": "IS_EXAM_MODE", "value": "true"},
      {"name": "MAX_CONCURRENT_EXECUTIONS", "value": "60"},
      {"name": "EXECUTION_TIMEOUT", "value": "30"},
      {"name": "MEMORY_LIMIT_MB", "value": "128"}
    ]
  }]' \
  --execution-role-arn arn:aws:iam::653306034507:role/ecsTaskExecutionRole \
  --task-role-arn arn:aws:iam::653306034507:role/ecsTaskRole \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --region us-east-2

# 2. Update service to use new task definition
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-exam-task-service \
  --task-definition pythonide-exam-task:LATEST \
  --force-new-deployment \
  --region us-east-2

# 3. Wait 2-3 minutes for deployment
```

---

### OPTION C: Combine Both (Best Practice - 10 Minutes)

**Recommended for Maximum Safety:**

```bash
# 1. Increase task definition to 2vCPU/4GB
# [Run Option B commands above]

# 2. Scale to 2 tasks
# [Run Option A commands above]

# 3. Verify both changes applied
aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-exam-task-service \
  --region us-east-2 | jq '.services[0] | {
    desiredCount,
    runningCount,
    taskDefinition,
    deployments
  }'
```

**Final Capacity with Option C:**
- 2 tasks × 2 vCPU each = **4 vCPU total**
- 2 tasks × 4 GB each = **8 GB total memory**
- Per-student: 235 MB RAM (vs 29 MB with current setup)
- Estimated CPU utilization: 15-20% (very safe)

---

## AWS Services Connected to Exam

### 1. **ECS (EC2 Container Service)** ✓
- **Service**: `pythonide-exam-task-service`
- **Cluster**: `pythonide-cluster`
- **Current Status**: Running (1 task)
- **Action Needed**: Scale to 2+ tasks

### 2. **ECS Task Definition** ✓
- **Family**: `pythonide-exam-task`
- **Current**: 1 vCPU / 2 GB per task
- **Action Needed**: Increase to 2 vCPU / 4 GB

### 3. **Application Load Balancer (ALB)** ✓
- **Name**: `pythonide-alb`
- **Target Group**: `pythonide-exam-tg` (port 8080)
- **Routing**: Host header `exam.pythonide-classroom.tech`
- **Health Check**: `/api/health` endpoint
- **Status**: Working correctly
- **Action Needed**: None (will automatically distribute 2 tasks)

### 4. **RDS PostgreSQL** ✓
- **Database**: `pythonide_exam` (separate from main)
- **Endpoint**: `pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com:5432`
- **Connection Pool**: Min 5, Max 25 connections
- **Current Usage**: ~10-15 connections for 34 students
- **Status**: Plenty of headroom ✓
- **Action Needed**: None (but monitor if load is very high)

### 5. **EFS (Elastic File System)** ✓
- **Mount Point**: `/mnt/efs/pythonide-data-exam`
- **Separate from Main IDE**: Yes (isolated data)
- **Status**: Both tasks will see same file data ✓
- **Action Needed**: None

### 6. **ECR (Elastic Container Registry)** ✓
- **Image**: `pythonide-exam:latest`
- **Registry**: `653306034507.dkr.ecr.us-east-2.amazonaws.com`
- **Status**: Image should be built and ready
- **Action Needed**: Verify image is present, built recently

### 7. **VPC & Security Groups** ✓
- **Cluster Security Group**: Allows port 8080 ingress
- **RDS Security Group**: Allows DB connections from ECS
- **Status**: Pre-configured and working
- **Action Needed**: None

---

## VERIFICATION CHECKLIST (Before Exam Starts)

**5 Minutes Before Exam:**

```bash
# 1. Check task status
aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-exam-task-service \
  --region us-east-2

# Verify: DesiredCount ≥ 2, RunningCount ≥ 2, all tasks healthy

# 2. Check load balancer health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-2:653306034507:targetgroup/pythonide-exam-tg/e058f73271f1595b \
  --region us-east-2

# Verify: All targets showing "healthy"

# 3. Check database connectivity
psql -h pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com \
  -U pythonide_admin \
  -d pythonide_exam \
  -c "SELECT current_timestamp;" && echo "✓ DB Connected"

# 4. Test exam URL in browser
# Visit: https://exam.pythonide-classroom.tech
# Try: Login with one student account, run simple code

# 5. Monitor CloudWatch (optional)
# AWS Console > CloudWatch > Logs > Filter: pythonide-exam
```

---

## POST-EXAM CLEANUP

**After Exam Ends:**

```bash
# 1. Scale back to 1 task (cost savings)
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-exam-task-service \
  --desired-count 1 \
  --region us-east-2

# 2. Review logs for any issues
aws logs tail /aws/ecs/pythonide-exam --follow

# 3. Check student submissions
# Verify all students' code was saved to EFS

# 4. If you increased task definition, revert
# [Register original 1vCPU/2GB task definition]
```

---

## LONG-TERM RECOMMENDATIONS (After Exam)

### Critical:
1. **Enable Auto-Scaling** for exam service
   - Set min: 2 tasks, max: 6 tasks
   - Target CPU: 45%
   - Auto-scale based on demand

2. **Create Deployment Automation** (GitHub Actions)
   - Same pipeline as main service
   - Automatic image building and pushing

3. **Add Health Checks** to task definition
   - Endpoint: `/api/health`
   - Interval: 30 seconds
   - Timeout: 5 seconds
   - Healthy threshold: 2
   - Unhealthy threshold: 3

4. **Configure CloudWatch Alarms**
   - High CPU (>80% for 2+ minutes)
   - High memory (>75% for 2+ minutes)
   - Service deployment failures
   - RDS connection pool near limit

### Important:
1. **Load Testing** before next exam
   - Simulate 34+ concurrent students
   - Test with auto-scaling enabled
   - Verify no errors under peak load

2. **Database Optimization**
   - Increase connection pool to 50
   - Add indexes if needed
   - Monitor slow query logs

3. **Documentation Updates**
   - Add scaling procedures to EXAM_ENVIRONMENT_GUIDE.md
   - Document cost implications
   - Create runbooks for common issues

---

## COST IMPLICATIONS

### Current Setup (1 task × 1 vCPU/2GB):
- ECS Fargate: ~$35/month (always running)
- RDS: ~$100/month (shared with main IDE)
- EFS: ~$30/month (shared with main IDE)
- **Total**: ~$165/month

### With 2 Tasks (2 tasks × 1 vCPU/2GB):
- ECS Fargate: ~$70/month
- **Additional Cost**: ~$35/month (2x tasks)
- Only during exam period (1-2 hours)

### With Scaled Definition (1 task × 2 vCPU/4GB):
- ECS Fargate: ~$70/month
- **Additional Cost**: ~$35/month
- Only during exam period (1-2 hours)

**Cost for 1 Exam (2 hours)**: ~$0.25 (negligible)

---

## SUMMARY

| Aspect | Current | Recommended |
|--------|---------|-------------|
| **Auto-Scaling** | ❌ None | ✓ 2-6 tasks |
| **Task Count** | 1 | 2-6 (auto) |
| **CPU per Task** | 1 vCPU | 1 vCPU (or 2) |
| **Memory per Task** | 2 GB | 4 GB (optional) |
| **Estimated CPU @ 34 students** | 60-70% (risky) | 15-35% (safe) |
| **Risk Level** | HIGH | LOW |
| **Implementation Time** | — | 5-10 minutes |

**RECOMMENDATION**: Execute Option A or C immediately (scale to 2 tasks). Takes 5 minutes and eliminates single point of failure.

