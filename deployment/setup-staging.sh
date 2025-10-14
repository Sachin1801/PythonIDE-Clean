#!/bin/bash

# Staging Environment Setup Script
# Run this step-by-step, verifying each command succeeds before proceeding

set -e  # Exit on any error

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Python IDE Staging Environment Setup${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="653306034507"
CLUSTER_NAME="pythonide-cluster"
PRODUCTION_SERVICE="pythonide-service"
STAGING_SERVICE="pythonide-staging-service"
STAGING_DB_INSTANCE="pythonide-staging-db"
STAGING_TASK_FAMILY="pythonide-staging-task"
EFS_ID="fs-0ba3b6fecab24774a"

echo -e "\n${YELLOW}Configuration:${NC}"
echo "  AWS Region: $AWS_REGION"
echo "  AWS Account: $AWS_ACCOUNT_ID"
echo "  ECS Cluster: $CLUSTER_NAME"
echo ""

# Step 1: Get VPC and Subnet information from production
echo -e "${BLUE}Step 1: Gathering production network configuration...${NC}"

read -p "Press Enter to continue..."

PROD_TASK_DEF=$(aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $PRODUCTION_SERVICE \
  --region $AWS_REGION \
  --query 'services[0].taskDefinition' \
  --output text 2>/dev/null || echo "")

if [ -z "$PROD_TASK_DEF" ]; then
    echo -e "${RED}Error: Could not get production task definition${NC}"
    echo "Please run: aws ecs describe-services --cluster $CLUSTER_NAME --services $PRODUCTION_SERVICE --region $AWS_REGION"
    exit 1
fi

echo -e "${GREEN}✓ Production task definition: $PROD_TASK_DEF${NC}"

# Get network configuration from production service
echo -e "\n${BLUE}Getting VPC and subnet configuration from production...${NC}"

NETWORK_CONFIG=$(aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $PRODUCTION_SERVICE \
  --region $AWS_REGION \
  --query 'services[0].networkConfiguration.awsvpcConfiguration' \
  --output json 2>/dev/null)

if [ -z "$NETWORK_CONFIG" ]; then
    echo -e "${RED}Error: Could not get network configuration${NC}"
    exit 1
fi

# Extract subnets and security groups
SUBNETS=$(echo $NETWORK_CONFIG | jq -r '.subnets | join(",")')
SECURITY_GROUPS=$(echo $NETWORK_CONFIG | jq -r '.securityGroups | join(",")')

echo -e "${GREEN}✓ Subnets: $SUBNETS${NC}"
echo -e "${GREEN}✓ Security Groups: $SECURITY_GROUPS${NC}"

# Save to file for reference
cat > /tmp/staging-config.json <<EOF
{
  "subnets": "$SUBNETS",
  "securityGroups": "$SECURITY_GROUPS",
  "region": "$AWS_REGION",
  "cluster": "$CLUSTER_NAME"
}
EOF

echo -e "${GREEN}✓ Configuration saved to /tmp/staging-config.json${NC}"

# Step 2: Create Staging RDS Database
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Step 2: Creating Staging RDS Database${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${YELLOW}This will create a db.t4g.micro PostgreSQL instance${NC}"
echo -e "${YELLOW}Estimated cost: ~$12-14/month${NC}"
echo ""

read -p "Do you want to create staging RDS? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}Creating staging database...${NC}"

    # Generate a random password
    STAGING_DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

    aws rds create-db-instance \
      --db-instance-identifier $STAGING_DB_INSTANCE \
      --db-instance-class db.t4g.micro \
      --engine postgres \
      --engine-version 15.7 \
      --master-username pythonide_admin \
      --master-user-password "$STAGING_DB_PASSWORD" \
      --allocated-storage 20 \
      --storage-type gp2 \
      --backup-retention-period 0 \
      --no-multi-az \
      --publicly-accessible false \
      --vpc-security-group-ids $(echo $SECURITY_GROUPS | cut -d',' -f1) \
      --db-name pythonide \
      --region $AWS_REGION \
      --tags Key=Environment,Value=staging Key=Project,Value=PythonIDE

    echo -e "${GREEN}✓ RDS creation initiated${NC}"
    echo -e "${YELLOW}⏳ This will take 5-10 minutes...${NC}"
    echo ""
    echo -e "${RED}IMPORTANT: Save this password!${NC}"
    echo "Staging DB Password: $STAGING_DB_PASSWORD"
    echo ""
    echo "Save to: deployment/staging-db-password.txt"
    echo "$STAGING_DB_PASSWORD" > deployment/staging-db-password.txt
    chmod 600 deployment/staging-db-password.txt
    echo -e "${GREEN}✓ Password saved to deployment/staging-db-password.txt${NC}"

    # Wait for RDS to be available
    echo -e "\n${YELLOW}Waiting for RDS to be available (this takes ~8 minutes)...${NC}"
    aws rds wait db-instance-available \
      --db-instance-identifier $STAGING_DB_INSTANCE \
      --region $AWS_REGION

    echo -e "${GREEN}✓ RDS database is ready!${NC}"

    # Get the endpoint
    STAGING_DB_ENDPOINT=$(aws rds describe-db-instances \
      --db-instance-identifier $STAGING_DB_INSTANCE \
      --region $AWS_REGION \
      --query 'DBInstances[0].Endpoint.Address' \
      --output text)

    echo -e "${GREEN}✓ Database endpoint: $STAGING_DB_ENDPOINT${NC}"
    echo ""
    echo "DATABASE_URL=postgresql://pythonide_admin:$STAGING_DB_PASSWORD@$STAGING_DB_ENDPOINT:5432/pythonide"

    # Save to config
    echo "$STAGING_DB_ENDPOINT" > /tmp/staging-db-endpoint.txt
    echo "$STAGING_DB_PASSWORD" > /tmp/staging-db-password.txt

else
    echo -e "${YELLOW}Skipping RDS creation${NC}"
    echo "You can create it later or use an existing database"

    read -p "Enter staging database endpoint (or press Enter to skip): " STAGING_DB_ENDPOINT
    read -p "Enter staging database password (or press Enter to skip): " STAGING_DB_PASSWORD
fi

# Step 3: Create Staging Task Definition
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Step 3: Creating Staging Task Definition${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${YELLOW}Creating staging task definition (0.5 vCPU, 1GB RAM)...${NC}"

# Get the latest production task definition
aws ecs describe-task-definition \
  --task-definition pythonide-task \
  --region $AWS_REGION \
  --query 'taskDefinition' > /tmp/prod-task-def.json

# Modify for staging
cat /tmp/prod-task-def.json | jq \
  --arg db_url "postgresql://pythonide_admin:$STAGING_DB_PASSWORD@$STAGING_DB_ENDPOINT:5432/pythonide" \
  '{
    family: "pythonide-staging-task",
    taskRoleArn: .taskRoleArn,
    executionRoleArn: .executionRoleArn,
    networkMode: .networkMode,
    requiresCompatibilities: .requiresCompatibilities,
    cpu: "512",
    memory: "1024",
    containerDefinitions: [
      .containerDefinitions[0] |
      .environment = (
        .environment |
        map(if .name == "DATABASE_URL" then .value = $db_url
            elif .name == "ENVIRONMENT" then .value = "staging"
            else . end) +
        [{name: "ENVIRONMENT", value: "staging"}]
      )
    ],
    volumes: .volumes
  }' > deployment/staging-task-definition.json

echo -e "${GREEN}✓ Staging task definition created: deployment/staging-task-definition.json${NC}"

# Register the task definition
echo -e "${YELLOW}Registering staging task definition...${NC}"

aws ecs register-task-definition \
  --cli-input-json file://deployment/staging-task-definition.json \
  --region $AWS_REGION

echo -e "${GREEN}✓ Staging task definition registered${NC}"

# Step 4: Create Staging ECS Service
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Step 4: Creating Staging ECS Service${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${YELLOW}Creating staging service (0 tasks initially)...${NC}"

# Get target group ARN from production ALB
PROD_TARGET_GROUP=$(aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $PRODUCTION_SERVICE \
  --region $AWS_REGION \
  --query 'services[0].loadBalancers[0].targetGroupArn' \
  --output text)

echo -e "${YELLOW}Note: Staging will share the same ALB, we'll add a separate listener rule${NC}"

# Create the service
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $STAGING_SERVICE \
  --task-definition $STAGING_TASK_FAMILY \
  --desired-count 0 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={
    subnets=[$SUBNETS],
    securityGroups=[$SECURITY_GROUPS],
    assignPublicIp=ENABLED
  }" \
  --region $AWS_REGION \
  --tags key=Environment,value=staging key=Project,value=PythonIDE

echo -e "${GREEN}✓ Staging service created (0 tasks running)${NC}"

# Step 5: Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}✅ Staging Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${GREEN}Resources Created:${NC}"
echo "  ✓ RDS Database: $STAGING_DB_INSTANCE"
echo "  ✓ Task Definition: $STAGING_TASK_FAMILY"
echo "  ✓ ECS Service: $STAGING_SERVICE (0 tasks)"
echo ""
echo -e "${YELLOW}Important Files:${NC}"
echo "  • deployment/staging-task-definition.json"
echo "  • deployment/staging-db-password.txt (KEEP SECURE!)"
echo "  • /tmp/staging-config.json"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Start staging: aws ecs update-service --cluster $CLUSTER_NAME --service $STAGING_SERVICE --desired-count 1 --region $AWS_REGION"
echo "  2. Check status: aws ecs describe-services --cluster $CLUSTER_NAME --services $STAGING_SERVICE --region $AWS_REGION"
echo "  3. Test staging: curl http://[TASK-IP]:8080/health"
echo "  4. Stop staging: aws ecs update-service --cluster $CLUSTER_NAME --service $STAGING_SERVICE --desired-count 0 --region $AWS_REGION"
echo ""
echo -e "${GREEN}✓ Setup complete! Staging environment ready for testing.${NC}"