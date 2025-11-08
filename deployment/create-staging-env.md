# Create AWS Staging Environment

## Option A: Use Separate ECS Service (Same Cluster)

```bash
# 1. Build and push staging image
docker build --platform linux/amd64 -f Dockerfile -t pythonide-backend:staging .
docker tag pythonide-backend:staging 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:staging
docker push 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:staging

# 2. Create staging task definition (modify existing)
# Edit task definition to use :staging tag instead of :latest

# 3. Create staging service on same cluster
aws ecs create-service \
  --cluster pythonide-cluster \
  --service-name pythonide-service-staging \
  --task-definition pythonide-task-staging \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --region us-east-2

# 4. Access via different port or ALB target group
```

## Option B: Use Same Service, Different Tag (Faster)

```bash
# 1. Push as staging tag
docker build --platform linux/amd64 -f Dockerfile -t pythonide-backend:staging .
docker tag pythonide-backend:staging 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:staging
docker push 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-backend:staging

# 2. Update ONLY your test user's task to use staging image
# Manually update task definition to use :staging tag
# Run single task instead of full service update

# 3. Connect to staging container
aws ecs execute-command \
  --cluster pythonide-cluster \
  --task <task-id> \
  --container pythonide \
  --interactive \
  --command "/bin/sh"
```

## Recommendation

For quick testing, **use local Docker Compose** - it's faster and safer!
- No AWS costs
- Faster iteration
- No risk to production
- Full control

Only create staging AWS environment if you need to test:
- AWS-specific features (EFS, RDS)
- Load balancing
- Auto-scaling
- Multiple concurrent users
