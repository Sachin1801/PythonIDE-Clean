# 🔄 Rollback Procedure for Tornado Multi-Process Optimization

## Quick Rollback (2 minutes)

If you notice any issues after deploying the multi-process optimization:

### Method 1: Environment Variable (Fastest - No Code Change)
```bash
# Simply set TORNADO_PROCESSES back to 1
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-service \
  --task-definition pythonide-task \
  --environment-overrides '[{
    "name": "pythonide-backend",
    "environment": [{"name": "TORNADO_PROCESSES", "value": "1"}]
  }]' \
  --force-new-deployment
```

### Method 2: Git Revert (5 minutes)
```bash
# Revert the commit that added multi-process support
git revert HEAD  # If it was the last commit
git push origin main

# GitHub Actions will automatically redeploy
```

### Method 3: Task Definition Rollback (3 minutes)
```bash
# Get the previous task definition revision
aws ecs describe-task-definition \
  --task-definition pythonide-task \
  --query 'taskDefinition.revision'

# Let's say current is revision 10, rollback to 9
aws ecs update-service \
  --cluster pythonide-cluster \
  --service pythonide-service \
  --task-definition pythonide-task:9 \
  --force-new-deployment
```

## Monitoring After Deployment

### Check if Multi-Process is Working
```bash
# SSH into container (if ECS Exec is enabled) or check logs
aws logs tail /ecs/pythonide --follow --filter-pattern "Started Tornado"

# Should see: "Started Tornado with 2 process(es)"
```

### Signs That Rollback is Needed

1. **High Error Rate**
   ```bash
   aws logs tail /ecs/pythonide --filter-pattern ERROR --since 1h
   ```

2. **WebSocket Connection Issues**
   - Students reporting "Connection lost" frequently
   - Check CloudWatch for WebSocket errors

3. **Session/Login Problems**
   - Students getting logged out unexpectedly
   - Database connection errors

4. **Performance Degradation**
   - Response times > 3 seconds
   - CPU usage > 80% consistently

## Verification After Rollback

```bash
# 1. Check service is stable
aws ecs describe-services \
  --cluster pythonide-cluster \
  --services pythonide-service \
  --query 'services[0].deployments'

# 2. Verify single-process mode
aws logs tail /ecs/pythonide --filter-pattern "single-process mode"

# 3. Test student login
curl -X POST http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test_student","password":"test123"}'

# 4. Check health endpoint
curl http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com/health
```

## Emergency Contact Plan

If rollback doesn't work:

1. **Immediate**: Set desired count to 0, then back to 2
   ```bash
   aws ecs update-service --cluster pythonide-cluster --service pythonide-service --desired-count 0
   sleep 10
   aws ecs update-service --cluster pythonide-cluster --service pythonide-service --desired-count 2
   ```

2. **Nuclear Option**: Redeploy from last known good commit
   ```bash
   git checkout [last-known-good-commit]
   git push --force origin main
   ```

3. **Manual Override**: Update task definition environment directly in AWS Console
   - Go to ECS → Task Definitions → pythonide-task
   - Create new revision
   - Set TORNADO_PROCESSES = 1
   - Update service to use new revision

## Rollback Decision Tree

```
Is the IDE completely down?
├─ YES → Emergency rollback (Method 1)
└─ NO → Are students experiencing issues?
    ├─ YES → Is it affecting > 50% of students?
    │   ├─ YES → Immediate rollback (Method 1)
    │   └─ NO → Monitor for 30 mins, then decide
    └─ NO → Are error rates elevated?
        ├─ YES (>5% errors) → Rollback (Method 2)
        └─ NO → Continue monitoring
```

## Post-Rollback Actions

1. **Document the issue**
   - What symptoms were observed?
   - What time did it occur?
   - How many students were affected?

2. **Analyze logs**
   ```bash
   aws logs get-log-events \
     --log-group-name /ecs/pythonide \
     --log-stream-name [stream-name] \
     --start-time [timestamp]
   ```

3. **Test fix locally before re-attempting**
   ```bash
   ./test_optimization.sh
   ```

## Prevention Checklist

Before deploying to production:

- [ ] Tested locally with 50+ simulated students
- [ ] Verified WebSocket connections remain stable
- [ ] Checked session management works correctly
- [ ] Confirmed database connections don't exceed limits
- [ ] Staging environment tested for 2+ hours
- [ ] CloudWatch alarms configured
- [ ] Rollback procedure reviewed

---

**Remember**: The optimization is controlled by an environment variable, so rollback is as simple as setting `TORNADO_PROCESSES=1` and redeploying. No code changes needed!