# RAG Project Terraform Infrastructure

This directory contains Terraform configuration for deploying the RAG application infrastructure on AWS.

## Architecture

The infrastructure includes:
- **EC2 Instance** (t3.small): Hosts Docker Compose with RAG API and Chatbot services
- **PostgreSQL RDS** (db.t3.micro): Managed database for conversations
- **ECR Repositories**: Container registries for RAG API and Chatbot images
- **Security Groups**: Network access control
- **IAM Roles**: EC2 permissions for ECR and SSM access
- **SSM Parameter Store**: Secure storage for secrets
- **Elastic IP**: Static IP address for the EC2 instance

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Terraform** version >= 1.0 installed
4. **EC2 Key Pair** created in your AWS account

### Create EC2 Key Pair

```bash
# Create a new key pair (if you don't have one)
aws ec2 create-key-pair --key-name rag-project-key --query 'KeyMaterial' --output text > ~/.ssh/rag-project-key.pem
chmod 400 ~/.ssh/rag-project-key.pem
```

### Bootstrap S3 Backend

Before running Terraform, create the S3 bucket for state management:

```bash
# Create S3 bucket
aws s3 mb s3://terraform-rag-project-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket terraform-rag-project-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket terraform-rag-project-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create DynamoDB table for state locking (optional but recommended)
aws dynamodb create-table \
  --table-name terraform-state-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## Deployment

### 1. Configure Variables

```bash
# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit variables
nano terraform.tfvars
```

**Important:** Update `developer_ip` with your actual IP address:
```bash
# Get your current IP
curl https://checkip.amazonaws.com
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Create ECR Repositories First

Create ECR repositories before the EC2 instance so you can push images:

```bash
terraform apply -target=aws_ecr_repository.rag_api -target=aws_ecr_repository.chatbot
```

### 4. Build and Push Docker Images

From the project root directory:

```bash
cd ..
make deploy
```

This will:
- Build Docker images
- Login to ECR
- Tag images
- Push to ECR

### 5. Deploy Complete Infrastructure

```bash
cd terraform
terraform plan
terraform apply
```

Review the plan carefully before confirming.

### 6. Set External Service Credentials

After infrastructure is created, set your OpenAI and Milvus credentials:

```bash
# Set OpenAI API Key
aws ssm put-parameter \
  --name "/rag-project/openai/api-key" \
  --value "YOUR_OPENAI_API_KEY" \
  --type SecureString \
  --overwrite

# Set Milvus URI
aws ssm put-parameter \
  --name "/rag-project/milvus/uri" \
  --value "YOUR_MILVUS_URI" \
  --type SecureString \
  --overwrite

# Set Milvus Token
aws ssm put-parameter \
  --name "/rag-project/milvus/token" \
  --value "YOUR_MILVUS_TOKEN" \
  --type SecureString \
  --overwrite
```

### 7. Deploy to EC2

The EC2 instance will attempt to deploy automatically via user data. If ECR was empty during creation, manually trigger deployment:

```bash
# Get the EC2 IP from Terraform output
EC2_IP=$(terraform output -raw elastic_ip)

# Deploy using the deploy script
cd ..
EC2_HOST=$EC2_IP SSH_KEY=~/.ssh/rag-project-key.pem ./scripts/deploy.sh
```

Or SSH to EC2 and deploy manually:

```bash
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$EC2_IP
cd /opt/rag-project
sudo ./deploy.sh
```

## Accessing the Application

After deployment, get the access URLs:

```bash
terraform output deployment_info
```

- **Chatbot UI**: `http://<elastic-ip>:8501`
- **RAG API**: `http://<elastic-ip>:8000`
- **API Docs**: `http://<elastic-ip>:8000/docs`

## Managing the Infrastructure

### View Outputs

```bash
terraform output
```

### Update Infrastructure

```bash
terraform plan
terraform apply
```

### Retrieve Secrets

```bash
# Database password
aws ssm get-parameter --name "/rag-project/database/password" --with-decryption --query "Parameter.Value" --output text

# All database credentials
aws ssm get-parameters-by-path --path "/rag-project/database" --with-decryption
```

### SSH to EC2

```bash
# Get SSH command
terraform output ssh_command

# Or manually
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$(terraform output -raw elastic_ip)
```

### Check Application Status

```bash
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$(terraform output -raw elastic_ip) << 'EOF'
  cd /opt/rag-project
  docker-compose ps
  docker-compose logs --tail=50
EOF
```

### Restart Services

```bash
ssh -i ~/.ssh/rag-project-key.pem ec2-user@$(terraform output -raw elastic_ip) << 'EOF'
  cd /opt/rag-project
  docker-compose restart
EOF
```

## CI/CD with GitHub Actions

The project includes a GitHub Actions workflow (`.github/workflows/deploy.yml`) that automatically:
1. Builds Docker images
2. Pushes to ECR
3. Deploys to EC2 (optional)

### Setup GitHub Secrets

Add these secrets to your GitHub repository:

- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (e.g., us-east-1)
- `EC2_HOST`: EC2 Elastic IP (optional)
- `EC2_SSH_PRIVATE_KEY`: SSH private key content (optional)

## Troubleshooting

### EC2 Instance Not Starting Services

```bash
# Check user data logs
ssh -i ~/.ssh/rag-project-key.pem ec2-user@<ip>
sudo cat /var/log/user-data.log

# Check service status
sudo systemctl status rag-project.service

# Manually start services
cd /opt/rag-project
sudo ./deploy.sh
```

### Cannot Connect to Database

```bash
# Verify security group allows your IP
aws ec2 describe-security-groups \
  --group-ids $(terraform output -raw rds_security_group_id) \
  --query 'SecurityGroups[0].IpPermissions'

# Test connection
psql -h $(terraform output -raw rds_address) \
     -U rag_admin \
     -d rag_db
```

### Docker Images Not Pulling

```bash
# Verify ECR repositories have images
aws ecr describe-images --repository-name rag-api
aws ecr describe-images --repository-name chatbot

# Check EC2 IAM role has ECR permissions
aws iam get-role-policy --role-name rag-project-ec2-role --policy-name rag-project-ecr-policy
```

## Cost Estimation

Monthly costs (us-east-1, approximate):
- EC2 t3.small: ~$15
- RDS db.t3.micro: ~$15
- EBS Storage (30GB): ~$3
- RDS Storage (20GB): ~$2.30
- Data Transfer: Variable
- **Total**: ~$35-40/month

## Security Considerations

- ✅ All secrets stored in SSM Parameter Store
- ✅ RDS and EC2 storage encrypted
- ✅ IMDSv2 required on EC2
- ✅ Security groups restrict access
- ⚠️ Update `developer_ip` to your specific IP
- ⚠️ RDS is publicly accessible (for development convenience)
- ⚠️ Consider adding authentication to the applications for production

## Cleanup

To destroy all infrastructure:

```bash
# WARNING: This will delete all data!
# First, disable prevent_destroy on RDS
# Edit database.tf and comment out the lifecycle block

terraform destroy
```

To destroy specific resources:

```bash
terraform destroy -target=aws_instance.app_server
```

## Support

For issues or questions:
1. Check CloudWatch Logs: `/ec2/rag-project/app-logs`
2. Review EC2 user data logs: `/var/log/user-data.log`
3. Check Docker logs: `docker-compose logs`
4. Verify IAM permissions and security groups

## License

Internal project - proprietary.

