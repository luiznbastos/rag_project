# RAG Project Deployment Guide

Complete guide for deploying the RAG application to AWS.

## Quick Start

```bash
# 1. Setup AWS infrastructure
cd terraform
terraform init
terraform apply -target=aws_ecr_repository.rag_api -target=aws_ecr_repository.chatbot

# 2. Build and push Docker images
cd ..
make deploy

# 3. Deploy complete infrastructure
cd terraform
terraform apply

# 4. Set external credentials
aws ssm put-parameter --name "/rag-project/openai/api-key" --value "YOUR_KEY" --type SecureString --overwrite
aws ssm put-parameter --name "/rag-project/milvus/uri" --value "YOUR_URI" --type SecureString --overwrite
aws ssm put-parameter --name "/rag-project/milvus/token" --value "YOUR_TOKEN" --type SecureString --overwrite

# 5. Access your application
# Get URLs from: terraform output deployment_info
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         GitHub Actions                       │
│  (Build → Push to ECR → Deploy to EC2)                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS Infrastructure                        │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   ECR Registry   │         │   SSM Parameter  │         │
│  │  - rag-api:latest│         │      Store       │         │
│  │  - chatbot:latest│         │   (Secrets)      │         │
│  └──────────────────┘         └──────────────────┘         │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   EC2 Instance   │────────▶│  PostgreSQL RDS  │         │
│  │  (Docker Compose)│         │   (Conversations)│         │
│  │                  │         └──────────────────┘         │
│  │  ┌────────────┐  │                                      │
│  │  │  RAG API   │  │◀────┐                                │
│  │  │  :8000     │  │     │                                │
│  │  └────────────┘  │     │                                │
│  │  ┌────────────┐  │     │                                │
│  │  │  Chatbot   │  │─────┘                                │
│  │  │  :8501     │  │                                      │
│  │  └────────────┘  │                                      │
│  └──────────────────┘                                      │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   Elastic IP     │         │  External APIs   │         │
│  │  (Static Public) │         │  - OpenAI        │         │
│  └──────────────────┘         │  - Milvus        │         │
│                                └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. AWS Setup

- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- EC2 Key Pair created

```bash
# Configure AWS CLI
aws configure

# Create key pair
aws ec2 create-key-pair \
  --key-name rag-project-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/rag-project-key.pem
chmod 400 ~/.ssh/rag-project-key.pem
```

### 2. Local Tools

- Terraform >= 1.0
- Docker and Docker Compose
- Make
- Git

```bash
# Verify installations
terraform --version
docker --version
docker-compose --version
make --version
```

### 3. External Services

- OpenAI API Key
- Milvus Cloud Instance (URI and Token)

## Step-by-Step Deployment

### Phase 1: Bootstrap

Create S3 bucket for Terraform state:

```bash
# Create bucket
aws s3 mb s3://terraform-rag-project-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket terraform-rag-project-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name terraform-state-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Phase 2: Configure

```bash
# Copy and edit Terraform variables
cd terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars

# Update these values:
# - developer_ip: Your IP from curl https://checkip.amazonaws.com
# - key_pair_name: Your EC2 key pair name
```

### Phase 3: Infrastructure - ECR

Create ECR repositories first:

```bash
cd terraform
terraform init
terraform apply -target=aws_ecr_repository.rag_api -target=aws_ecr_repository.chatbot
```

### Phase 4: Build and Push Images

```bash
cd ..  # Back to project root
make deploy
```

This will:
- Build both Docker images
- Login to ECR
- Tag images with latest and commit SHA
- Push to ECR

### Phase 5: Complete Infrastructure

```bash
cd terraform
terraform plan    # Review changes
terraform apply   # Deploy
```

This creates:
- PostgreSQL RDS instance
- EC2 instance with Docker Compose
- Security groups
- IAM roles
- SSM parameters
- Elastic IP

### Phase 6: Configure Secrets

```bash
# OpenAI API Key
aws ssm put-parameter \
  --name "/rag-project/openai/api-key" \
  --value "sk-..." \
  --type SecureString \
  --overwrite

# Milvus URI
aws ssm put-parameter \
  --name "/rag-project/milvus/uri" \
  --value "https://your-cluster.api.gcp-starter.zillizcloud.com" \
  --type SecureString \
  --overwrite

# Milvus Token
aws ssm put-parameter \
  --name "/rag-project/milvus/token" \
  --value "your-token" \
  --type SecureString \
  --overwrite
```

### Phase 7: Verify Deployment

```bash
# Get deployment info
cd terraform
terraform output deployment_info

# Check EC2 status
EC2_IP=$(terraform output -raw elastic_ip)
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP << 'EOF'
  cd /opt/rag-project
  docker-compose ps
  docker-compose logs --tail=20
EOF
```

### Phase 8: Access Application

```bash
# Get URLs
terraform output chatbot_url
terraform output rag_api_docs_url

# Open in browser
# Chatbot: http://<ip>:8501
# API Docs: http://<ip>:8000/docs
```

## Continuous Deployment

### Local Deployment

After making changes:

```bash
# Build and push new images
make deploy

# Deploy to EC2
EC2_HOST=$(cd terraform && terraform output -raw elastic_ip)
EC2_HOST=$EC2_HOST SSH_KEY=~/.ssh/rag-project-key.pem ./scripts/deploy.sh
```

### GitHub Actions (Recommended)

1. **Setup GitHub Secrets**:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `EC2_HOST` (optional)
   - `EC2_SSH_PRIVATE_KEY` (optional)

2. **Automatic Deployment**:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

GitHub Actions will automatically:
- Build Docker images
- Push to ECR
- Deploy to EC2 (if configured)

## Operations

### Update Application Code

```bash
# Option 1: GitHub Actions (automatic)
git push origin main

# Option 2: Manual
make deploy
cd terraform
EC2_IP=$(terraform output -raw elastic_ip)
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP \
  'cd /opt/rag-project && sudo ./deploy.sh'
```

### View Logs

```bash
EC2_IP=$(cd terraform && terraform output -raw elastic_ip)

# Application logs
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP \
  'cd /opt/rag-project && docker-compose logs -f'

# RAG API logs only
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP \
  'cd /opt/rag-project && docker-compose logs -f rag-api'

# Chatbot logs only
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP \
  'cd /opt/rag-project && docker-compose logs -f chatbot'
```

### Restart Services

```bash
EC2_IP=$(cd terraform && terraform output -raw elastic_ip)

ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP << 'EOF'
  cd /opt/rag-project
  docker-compose restart
EOF
```

### Database Access

```bash
# Get credentials
aws ssm get-parameter --name "/rag-project/database/password" --with-decryption

# Connect
RDS_HOST=$(cd terraform && terraform output -raw rds_address)
psql -h $RDS_HOST -U rag_admin -d rag_db
```

### Scale Resources

Update `terraform.tfvars`:
```hcl
instance_type     = "t3.medium"  # Upgrade from t3.small
db_instance_class = "db.t3.small"  # Upgrade from db.t3.micro
```

Apply changes:
```bash
cd terraform
terraform plan
terraform apply
```

## Monitoring

### CloudWatch Logs

```bash
# View logs
aws logs tail /ec2/rag-project/app-logs --follow

# Query logs
aws logs filter-log-events \
  --log-group-name /ec2/rag-project/app-logs \
  --filter-pattern "ERROR"
```

### Health Checks

```bash
EC2_IP=$(cd terraform && terraform output -raw elastic_ip)

# RAG API health
curl http://$EC2_IP:8000/health

# Chatbot health
curl http://$EC2_IP:8501/_stcore/health
```

## Troubleshooting

### Services Not Starting

```bash
# Check user data execution
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP
sudo cat /var/log/user-data.log

# Check service status
sudo systemctl status rag-project.service

# Check Docker status
cd /opt/rag-project
docker-compose ps
docker-compose logs
```

### Images Not Found

```bash
# Verify images in ECR
aws ecr describe-images --repository-name rag-api
aws ecr describe-images --repository-name chatbot

# Manually pull on EC2
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP << 'EOF'
  cd /opt/rag-project
  aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin <ecr-registry>
  docker-compose pull
  docker-compose up -d
EOF
```

### Database Connection Issues

```bash
# Verify security group
aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=rag-project-rds-sg"

# Test from EC2
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP
docker run -it --rm postgres:15 psql -h <rds-host> -U rag_admin -d rag_db
```

## Cleanup

```bash
# Stop services on EC2
EC2_IP=$(cd terraform && terraform output -raw elastic_ip)
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP \
  'cd /opt/rag-project && docker-compose down'

# Destroy infrastructure
cd terraform

# Edit database.tf and comment out prevent_destroy
nano database.tf

# Destroy
terraform destroy
```

## Cost Optimization

- Use Spot instances for EC2 (requires additional configuration)
- Enable RDS storage autoscaling
- Use Reserved Instances for production
- Implement CloudWatch alarms for cost monitoring

## Security Best Practices

- ✅ Rotate database passwords regularly
- ✅ Update `developer_ip` to specific IP ranges
- ✅ Enable MFA for AWS account
- ✅ Review IAM permissions periodically
- ✅ Keep Docker images updated
- ✅ Enable AWS GuardDuty for threat detection
- ⚠️ Consider adding WAF for production
- ⚠️ Implement application-level authentication

## Support

For issues:
1. Check CloudWatch Logs
2. Review EC2 user data logs
3. Verify security groups and IAM roles
4. Test with manual Docker commands
5. Review Terraform state

## Next Steps

- Setup automated backups
- Configure CloudWatch alarms
- Implement log aggregation
- Setup monitoring dashboards
- Configure SSL/TLS certificates
- Implement rate limiting
- Setup automated testing

