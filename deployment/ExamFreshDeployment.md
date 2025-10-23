## This is a short guide to deploy after fresh changes manually on aws pythonide-exam

### Step 1 : Docker build the container locally for creating the latest image for ecr

`docker build --platform linux/amd64 -f Dockerfile -t pythonide-exam:latest .`

### Step 2 : Login to ecr

`aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 653306034507.dkr.ecr.us-east-2.amazonaws.com `

- In the end is the ECR URI

### Step 3 : Tag latest built image 

`docker tag pythonide-exam:latest 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-exam:latest`

### Step 4 : Push to exam ecr repository

`docker push 653306034507.dkr.ecr.us-east-2.amazonaws.com/pythonide-exam:latest`

### Step 2 : Deploy to ECS ( can be done manually on aws console too by upating the service with new image for the task)

`aws ecs update-service --cluster pythonide-cluster --service pythonide-exam-task-service --force-new-deployment --region us-east-2`



