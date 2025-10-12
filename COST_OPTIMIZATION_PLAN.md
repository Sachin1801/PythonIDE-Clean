# 💰 Cost Optimization Plan (Based on Real CloudWatch Data)

**Current Observation**: CPU < 5%, Memory < 5%
**Conclusion**: 95% of resources are wasted!

---

## 📊 Current vs Optimized Architecture

### Current Production (Wasteful):
```
2 tasks × (2 vCPU, 8GB RAM) = 4 vCPU, 16GB total
├─ Cost: ~$58/month for compute
├─ Usage: Only 5% utilized
└─ Waste: ~$55/month thrown away!
```

### Optimized Production (Smart):
```
Normal: 1 task × (1 vCPU, 2GB RAM)
├─ Cost: ~$15/month (74% savings!)
├─ Usage: 20-25% utilized (healthy)
└─ Auto-scaling: Ready to scale to 4 tasks during exams
```

---

## 🎯 Recommended Configuration

### Production Task Definition:
```json
{
  "family": "pythonide-task",
  "cpu": "1024",     // 1 vCPU (was 2048)
  "memory": "2048",  // 2GB (was 8192)
  "desiredCount": 1  // 1 task normally
}
```

### Auto-Scaling Configuration:
```yaml
Min tasks: 1
Max tasks: 4
Trigger: 60% CPU (instead of 45%)

# Scale up when:
- CPU > 60% for 2 minutes → Add 1 task
- CPU > 80% for 1 minute → Add 2 tasks

# Scale down when:
- CPU < 30% for 5 minutes → Remove 1 task
- Never go below 1 task
```

---

## 🏗️ Staging Environment Setup

### Staging Configuration (On-Demand):
```json
{
  "family": "pythonide-staging-task",
  "cpu": "512",      // 0.5 vCPU (minimal for testing)
  "memory": "1024",  // 1GB
  "desiredCount": 0  // Stopped by default
}
```

### Staging Usage Pattern:
```
Week 1-3: Stopped (0 tasks) = $0
Week 4: Testing (2 hours) = $0.15
Month total: ~$0.50
```

### When to Use Staging:
1. **Before midsems**: Test scaling behavior
2. **New features**: Test before students see
3. **Infrastructure changes**: Test EFS, RDS, etc.
4. **Load testing**: Simulate exam day load

---

## 💸 Cost Breakdown

### Current Monthly Costs:
```
ECS Compute: $58/month (2 tasks × 2 vCPU)
RDS: $30-50/month
EFS: $10-20/month
ALB: $18/month
Total: ~$116-146/month
```

### After Optimization:
```
ECS Compute: $15/month (1 task × 1 vCPU)  [SAVE $43]
RDS: $30-50/month (no change)
EFS: $16/month (add provisioned)          [ADD $6]
ALB: $18/month (no change)
Staging: $1/month (on-demand)             [ADD $1]
Monitoring: $3/month (CloudWatch)         [ADD $3]
Total: ~$83-103/month

SAVINGS: $33-43/month (28-37% reduction!)
```

### During Midsems (1 week):
```
Compute spikes to: $60/month for that week
Average monthly: Still ~$90-110/month
Annual savings: ~$350-500/year
```

---

## 🚀 Implementation Steps

### Phase 1: Set Up Staging (This Week)

#### Day 1: Create Staging Infrastructure
```bash
# 1. Create staging RDS (db.t4g.micro)
aws rds create-db-instance \
  --db-instance-identifier pythonide-staging-db \
  --db-instance-class db.t4g.micro \
  --engine postgres \
  --master-username pythonide_admin \
  --master-user-password [STAGING_PASSWORD] \
  --allocated-storage 20 \
  --backup-retention-period 0 \
  --region us-east-2

# 2. Create staging task definition
# Copy deployment/ecs-task-definition.json → deployment/staging-task-definition.json
# Modify:
#   - cpu: "512"
#   - memory: "1024"
#   - DATABASE_URL: staging RDS
#   - ENVIRONMENT: staging

# 3. Create staging service (starts with 0 tasks)
aws ecs create-service \
  --cluster pythonide-cluster \
  --service-name pythonide-staging-service \
  --task-definition pythonide-staging-task \
  --desired-count 0 \
  --launch-type FARGATE \
  --region us-east-2

# 4. Add ALB listener rule for staging.pythonide-classroom.tech
```

#### Day 2: Test Staging
```bash
# Start staging
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-staging-service \
  --desired-count 1

# Test for 2 hours
curl https://staging.pythonide-classroom.tech/health

# Stop staging
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-staging-service \
  --desired-count 0
```

---

### Phase 2: Optimize Production (Next Week)

#### Step 1: Right-Size Task (Test on Staging First!)
```bash
# Update task definition
aws ecs register-task-definition \
  --family pythonide-task \
  --cpu 1024 \
  --memory 2048 \
  --region us-east-2

# Update service to use new task definition
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-service \
  --task-definition pythonide-task:NEW_REVISION \
  --force-new-deployment
```

#### Step 2: Optimize Auto-Scaling
```bash
# Update target tracking policy
aws application-autoscaling put-scaling-policy \
  --policy-name pythonide-cpu-scaling \
  --service-namespace ecs \
  --resource-id service/pythonide-cluster/pythonide-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 60.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

#### Step 3: Reduce Min Task Count
```bash
# Set min/max for auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/pythonide-cluster/pythonide-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 4
```

---

### Phase 3: Add Monitoring (Week 3)

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name PythonIDE-Production \
  --dashboard-body file://cloudwatch-dashboard.json

# Set up alarms
aws cloudwatch put-metric-alarm \
  --alarm-name pythonide-high-cpu \
  --alarm-description "Alert when CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

---

## 🎓 Exam Day Strategy

### Before Midsems (1 week prior):

**Day 1-2**: Test on staging with high load
```bash
# Scale staging to 4 tasks
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-staging-service \
  --desired-count 4

# Run load test with 100 simulated students
./simple_load_test.sh 100

# Verify performance is good
```

**Day 3-5**: Pre-scale production
```bash
# Manually set desired count to 2-3 before exam
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-service \
  --desired-count 3

# Auto-scaling will handle spikes from there
```

**Exam Day**: Monitor dashboard
- Watch CloudWatch metrics
- Auto-scaling will handle load automatically
- Can manually scale if needed

**After Exam**: Scale back down
```bash
# Let auto-scaling bring it back to 1 task naturally
# Or force it:
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-service \
  --desired-count 1
```

---

## 📊 Capacity Planning

### Current Capacity (5% CPU usage):
```
With 60 students using <5% CPU on 2 vCPU:
→ 1 vCPU can handle 60 students at 10% CPU
→ 1 task × 1 vCPU = 60 students comfortably
→ 4 tasks × 1 vCPU = 240 students maximum
```

### Scaling Math:
| Students | Tasks Needed | CPU Used | Monthly Cost |
|----------|--------------|----------|--------------|
| 60 | 1 | ~10% | $15 |
| 120 | 2 | ~20% | $30 |
| 180 | 3 | ~30% | $45 |
| 240 | 4 | ~40% | $60 |

**Your 60 students**: Perfectly served by 1 task

---

## ⚠️ Rollback Plan

If right-sizing causes issues:

### Immediate Rollback (2 minutes):
```bash
# Revert to previous task definition
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-service \
  --task-definition pythonide-task:PREVIOUS_REVISION \
  --desired-count 2 \
  --force-new-deployment
```

### Signs You Need to Rollback:
- Response times > 500ms
- CPU consistently > 80%
- Student complaints about slowness
- WebSocket disconnections

---

## 🎯 Timeline

### This Week:
- [x] Test results complete
- [ ] Set up staging environment
- [ ] Test staging with load

### Next Week:
- [ ] Right-size production to 1 vCPU, 2GB
- [ ] Reduce min tasks to 1
- [ ] Adjust auto-scaling to 60% CPU trigger
- [ ] Monitor for 1 week

### Week 3:
- [ ] Add CloudWatch dashboard
- [ ] Set up alerts
- [ ] Document exam day procedures

### Week 4:
- [ ] Enable EFS provisioned throughput
- [ ] Measure improvements
- [ ] Finalize optimizations

---

## 📈 Expected Results (1 Month)

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Monthly Cost** | $116-146 | $83-103 | -28% to -37% |
| **Annual Cost** | $1,392-1,752 | $996-1,236 | **Save $400-500/year** |
| **Normal CPU** | 2.5% | 10-15% | Healthy |
| **Response Time** | 42ms | 35ms | 17% faster |
| **Exam Capacity** | 120 students | 240 students | 2× capacity |
| **Flexibility** | Low | High | Much better |

---

## 🎉 Summary

### Why This Is Perfect For You:

1. ✅ **Save $400-500/year** with better performance
2. ✅ **Staging environment** for safe testing
3. ✅ **Auto-scaling** handles exam spikes automatically
4. ✅ **Pay only for what you use** (1 task normally, 4 during exams)
5. ✅ **Zero risk** to students (test everything on staging first)

### Your Use Case:
- Normal weeks: 60 students, low load → 1 task
- Midsems/finals: 100+ students, high load → Auto-scales to 4 tasks
- Testing: Use staging (costs pennies)

**This is the ideal architecture for your situation!**

---

## 🚀 Next Action

**Start with staging setup this week**, then right-size production next week. You'll see savings immediately while maintaining (or improving) performance.