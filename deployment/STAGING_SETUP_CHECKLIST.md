# ✅ Staging Environment Setup Checklist

**Use this checklist to track your progress**

---

## 🎯 Prerequisites

- [ ] AWS Console access to account 653306034507
- [ ] AWS CLI configured (or ready to use Console)
- [ ] Production cluster running (pythonide-cluster)
- [ ] All setup scripts created (deployment/*.sh)

---

## 📋 Setup Steps

### Step 1: Create Staging RDS Database ⏱️ 15 mins

- [ ] Navigate to RDS Console → Create Database
- [ ] Select PostgreSQL 15.7
- [ ] Name: `pythonide-staging-db`
- [ ] Instance class: `db.t4g.micro`
- [ ] Master username: `pythonide_admin`
- [ ] Generate strong password → **Save it!**
- [ ] Storage: 20 GB gp2
- [ ] Same VPC/Security Group as production
- [ ] Database name: `pythonide`
- [ ] Backup retention: 0 days
- [ ] Multi-AZ: No
- [ ] Public access: No
- [ ] Click Create Database
- [ ] **Wait 8-10 minutes** for status: Available
- [ ] Copy endpoint URL
- [ ] Save password to: `deployment/staging-db-password.txt`

**Expected outcome**: RDS database available
**Cost**: ~$12-14/month

---

### Step 2: Create CloudWatch Log Group ⏱️ 2 mins

- [ ] Navigate to CloudWatch Console → Log groups
- [ ] Click Create log group
- [ ] Name: `/ecs/pythonide-staging`
- [ ] Retention: 7 days
- [ ] Click Create

**Expected outcome**: Log group created
**Cost**: ~$0.50/month

---

### Step 3: Create Staging Task Definition ⏱️ 10 mins

**Option A: Via AWS Console** (Easier)

- [ ] Navigate to ECS Console → Task Definitions
- [ ] Select `pythonide-task` → Create new revision
- [ ] Change family name to: `pythonide-staging-task`
- [ ] CPU: `512` (0.5 vCPU)
- [ ] Memory: `1024` (1 GB)
- [ ] Update container environment variables:
  - [ ] `DATABASE_URL`: Your staging database URL
  - [ ] `ENVIRONMENT`: `staging`
  - [ ] `TORNADO_PROCESSES`: `1`
- [ ] Update log configuration:
  - [ ] awslogs-group: `/ecs/pythonide-staging`
- [ ] Click Create

**Option B: Via JSON File**

- [ ] Use template from `deployment/STAGING_SETUP_MANUAL.md`
- [ ] Replace `YOUR_PASSWORD` with staging DB password
- [ ] Replace `YOUR_ENDPOINT` with staging DB endpoint
- [ ] Save as `deployment/staging-task-definition.json`
- [ ] Upload via AWS Console or CLI

**Expected outcome**: Task definition created
**Version**: Should be revision 1

---

### Step 4: Create Staging ECS Service ⏱️ 5 mins

- [ ] Navigate to ECS Console → Clusters → pythonide-cluster
- [ ] Click Create in Services tab
- [ ] Launch type: **Fargate**
- [ ] Task Definition: `pythonide-staging-task:1`
- [ ] Service name: `pythonide-staging-service`
- [ ] Number of tasks: **0** (start stopped)
- [ ] Deployment type: Rolling update
- [ ] VPC: Same as production
- [ ] Subnets: Select all available
- [ ] Security groups: Same as production
- [ ] Auto-assign public IP: **ENABLED**
- [ ] Load balancer: **None** (testing without ALB first)
- [ ] Click Create Service

**Expected outcome**: Service created with 0 tasks
**Status**: Should show ACTIVE

---

### Step 5: Test Staging Environment ⏱️ 10 mins

#### Start Staging:

**Via Script** (if AWS CLI works):
```bash
./deployment/start-staging.sh
```

**Via Console**:
- [ ] Go to ECS → pythonide-cluster → pythonide-staging-service
- [ ] Click Update
- [ ] Number of tasks: **1**
- [ ] Click Update Service
- [ ] Wait 2-3 minutes

#### Get Task IP:

- [ ] Go to Tasks tab
- [ ] Click on the running task
- [ ] Copy **Public IP** from Network section

#### Test Health Endpoint:

```bash
# Replace XX.XX.XX.XX with your task IP
curl http://XX.XX.XX.XX:8080/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "memory_percent": XX,
  "cpu_percent": XX
}
```

#### Check Logs:

- [ ] Go to CloudWatch → Log groups → `/ecs/pythonide-staging`
- [ ] Check latest log stream
- [ ] Verify server started successfully
- [ ] Look for: "Server listening on 0.0.0.0:8080"

#### Stop Staging:

**Via Script**:
```bash
./deployment/stop-staging.sh
```

**Via Console**:
- [ ] Go to ECS → pythonide-staging-service
- [ ] Click Update
- [ ] Number of tasks: **0**
- [ ] Click Update Service

**Expected outcome**: Task stopped, cost reduced to ~$12/month (RDS only)

---

## 🧪 Optional: Load Test on Staging

If everything works:

- [ ] Start staging: `./deployment/start-staging.sh`
- [ ] Get task IP from output
- [ ] Update `simple_load_test.sh` with staging IP
- [ ] Run load test: `./simple_load_test.sh 20`
- [ ] Verify performance is acceptable
- [ ] Stop staging: `./deployment/stop-staging.sh`

---

## 📊 Verification Checklist

After setup, verify:

- [ ] RDS database status: **Available**
- [ ] ECS service status: **Active**
- [ ] Task can start successfully
- [ ] Health endpoint returns 200 OK
- [ ] Database connection works
- [ ] Logs appear in CloudWatch
- [ ] Can stop/start staging on demand
- [ ] Helper scripts work correctly

---

## 💰 Cost Summary

| Resource | Status | Cost |
|----------|--------|------|
| RDS db.t4g.micro | Always on | $12-14/month |
| ECS Fargate (stopped) | 0 tasks | $0/hour |
| ECS Fargate (running) | 1 task | $0.04/hour |
| CloudWatch Logs | 7-day retention | ~$0.50/month |
| **Total (stopped)** | | **~$12-15/month** |
| **Total (testing 2hrs/month)** | | **~$12-15/month** |

---

## 📁 Files Created

- [ ] `deployment/setup-staging.sh` - Automated setup script
- [ ] `deployment/STAGING_SETUP_MANUAL.md` - Manual setup guide
- [ ] `deployment/start-staging.sh` - Start staging helper
- [ ] `deployment/stop-staging.sh` - Stop staging helper
- [ ] `deployment/staging-status.sh` - Check staging status
- [ ] `deployment/staging-db-password.txt` - Database password (SECURE!)
- [ ] `deployment/staging-task-definition.json` - Task definition

---

## 🚨 Troubleshooting

### Issue: Task won't start

**Check**:
- [ ] CloudWatch logs for errors
- [ ] Database endpoint is correct
- [ ] Security group allows port 5432
- [ ] Task has public IP assigned

**Solution**:
- Review logs in `/ecs/pythonide-staging`
- Verify DATABASE_URL in task definition
- Check security group rules

### Issue: Health check fails

**Check**:
- [ ] Task is in RUNNING state (not PENDING)
- [ ] Public IP is assigned
- [ ] Security group allows port 8080
- [ ] Wait 2-3 minutes after start

**Solution**:
- Wait for task to fully start
- Check logs for startup errors
- Verify security group inbound rules

### Issue: Database connection fails

**Check**:
- [ ] RDS status is "Available"
- [ ] DATABASE_URL is correct
- [ ] Password is correct
- [ ] Security group allows PostgreSQL traffic

**Solution**:
- Test connection from production task
- Verify RDS security group settings
- Check DATABASE_URL format

---

## 🎯 Next Steps After Setup

Once staging is working:

- [ ] Test code changes on staging before production
- [ ] Test cost optimizations (1 vCPU, 2GB)
- [ ] Test EFS provisioned throughput
- [ ] Practice exam day scaling
- [ ] Document staging procedures for team

---

## 📞 Quick Commands Reference

```bash
# Start staging
./deployment/start-staging.sh

# Check status
./deployment/staging-status.sh

# Stop staging
./deployment/stop-staging.sh

# View logs
aws logs tail /ecs/pythonide-staging --follow --region us-east-2

# Manual start
aws ecs update-service --cluster pythonide-cluster \
  --service pythonide-staging-service --desired-count 1 --region us-east-2

# Manual stop
aws ecs update-service --cluster pythonide-cluster \
  --service pythonide-staging-service --desired-count 0 --region us-east-2
```

---

## ✅ Success Criteria

Staging setup is complete when:

- [x] RDS database is available
- [x] ECS service can start tasks
- [x] Health endpoint returns 200 OK
- [x] Can start/stop on demand
- [x] CloudWatch logs are visible
- [x] Cost is ~$12-15/month when stopped

---

**Estimated Total Time**: 45-60 minutes
**Difficulty**: Medium
**Cost Impact**: +$12-15/month
**Value**: High (safe testing, prevent production issues)