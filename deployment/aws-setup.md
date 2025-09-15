# AWS Deployment with Persistent Data

## Overview
This guide ensures your Python IDE maintains persistent data across deployments on AWS.

## Architecture

### 1. **Database: AWS RDS PostgreSQL 15.7**
- All user accounts, passwords, sessions stored here
- Persists automatically across deployments
- Managed by AWS (automatic backups)

### 2. **File Storage: AWS EFS (Elastic File System)**
- All student files and folders stored here
- Persists across container restarts/deployments
- Shared across multiple containers if scaling

## Setup Steps

### Step 1: Create AWS EFS
```bash
# Create EFS filesystem
aws efs create-file-system \
    --performance-mode generalPurpose \
    --throughput-mode bursting \
    --tags "Key=Name,Value=pythonide-efs"

# Create mount targets in your VPC subnets
aws efs create-mount-target \
    --file-system-id fs-xxxxx \
    --subnet-id subnet-xxxxx \
    --security-groups sg-xxxxx
```

### Step 2: Update ECS Task Definition
```json
{
  "family": "pythonide-task",
  "containerDefinitions": [{
    "name": "pythonide",
    "image": "your-ecr-repo/pythonide:latest",
    "memory": 2048,
    "cpu": 1024,
    "environment": [
      {"name": "DATABASE_URL", "value": "postgresql://user:pass@rds-endpoint:5432/pythonide"},
      {"name": "IDE_SECRET_KEY", "value": "your-secret-key"}
    ],
    "mountPoints": [{
      "sourceVolume": "efs-storage",
      "containerPath": "/app/server/projects/ide"
    }]
  }],
  "volumes": [{
    "name": "efs-storage",
    "efsVolumeConfiguration": {
      "fileSystemId": "fs-xxxxx",
      "rootDirectory": "/"
    }
  }]
}
```

### Step 3: Initialize Users (First Time Only)
```bash
# SSH into ECS container or run as ECS task
docker exec -it <container-id> bash

# Run user creation script
cd /app/server
python migrations/create_real_class_users.py
python migrations/sync_user_directories.py
```

## Data Persistence Guarantee

### ✅ What Persists:
1. **User Accounts** - Stored in RDS PostgreSQL
2. **Passwords** - Hashed in RDS PostgreSQL  
3. **Student Files** - Stored in EFS at `/mnt/efs/`
4. **Student Folders** - Created in EFS, persist forever
5. **Sessions** - Stored in RDS PostgreSQL

### ❌ What Gets Reset:
- Nothing! All data persists across deployments

## Deployment Process

### For Code Updates:
```bash
# Build new Docker image
docker build -t pythonide:latest .

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <ecr-url>
docker tag pythonide:latest <ecr-url>/pythonide:latest
docker push <ecr-url>/pythonide:latest

# Update ECS service (triggers new deployment)
aws ecs update-service --cluster pythonide-cluster --service pythonide-service --force-new-deployment
```

### Important Notes:
1. **First Deployment**: Run user creation scripts once
2. **Subsequent Deployments**: Users and files persist automatically
3. **Backups**: 
   - RDS: Enable automated backups (7-day retention recommended)
   - EFS: Enable AWS Backup for file system backups

## Environment Variables for AWS

```env
# .env.aws
DATABASE_URL=postgresql://pythonide:password@pythonide.xxxxx.rds.amazonaws.com:5432/pythonide
IDE_SECRET_KEY=your-production-secret-key
AWS_REGION=us-east-1
EFS_MOUNT_PATH=/mnt/efs
```

## Cost Optimization

### Estimated Monthly Costs:
- **RDS db.t3.micro**: ~$15/month
- **EFS** (10GB): ~$3/month  
- **ECS Fargate** (1 vCPU, 2GB): ~$30/month
- **Total**: ~$48/month

### To Reduce Costs:
1. Use EC2 instead of Fargate (~$10/month for t3.micro)
2. Use RDS with reserved instances (1-year commitment)
3. Use EFS Infrequent Access for older files

## Monitoring

### CloudWatch Metrics to Track:
- RDS: Connection count, CPU, storage
- EFS: Throughput, burst credits
- ECS: CPU, memory utilization

### Alarms to Set:
```bash
# High database connections
aws cloudwatch put-metric-alarm \
    --alarm-name pythonide-db-connections \
    --alarm-description "Alert when DB connections > 50" \
    --metric-name DatabaseConnections \
    --namespace AWS/RDS \
    --statistic Average \
    --period 300 \
    --threshold 50 \
    --comparison-operator GreaterThanThreshold
```

## Disaster Recovery

### Backup Strategy:
1. **RDS**: Daily automated backups (7-day retention)
2. **EFS**: Weekly AWS Backup snapshots
3. **Code**: Git repository (GitHub/GitLab)

### Recovery Time:
- **RDS Restore**: ~10 minutes
- **EFS Restore**: ~5 minutes
- **Full System**: ~30 minutes

## Security Considerations

1. **Encryption at Rest**:
   - Enable RDS encryption
   - Enable EFS encryption

2. **Network Security**:
   - RDS in private subnet
   - EFS mount targets in private subnets
   - Application Load Balancer in public subnet

3. **Secrets Management**:
   - Use AWS Secrets Manager for DATABASE_URL
   - Use AWS Systems Manager Parameter Store for config

## Testing Persistence

### Test Procedure:
1. Login as student, create files
2. Deploy new version of code
3. Login again - files should still exist
4. Check database - all users should persist

### Verification Commands:
```bash
# Check EFS mount
docker exec <container-id> ls -la /app/server/projects/ide/Local/

# Check database users
docker exec <container-id> python -c "
from common.database import db_manager
users = db_manager.execute_query('SELECT username, role FROM users')
for u in users: print(f'{u['username']}: {u['role']}')
"
```