#!/bin/bash
set -e

# Log everything
exec > >(tee -a /var/log/user-data.log)
exec 2>&1

echo "=========================================="
echo "Starting RAG Project EC2 initialization"
echo "Date: $(date)"
echo "=========================================="

# Update system
echo "Updating system packages..."
dnf update -y

# Install Docker
echo "Installing Docker..."
dnf install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
echo "Installing Docker Compose..."
DOCKER_COMPOSE_VERSION="2.24.0"
curl -L "https://github.com/docker/compose/releases/download/v$${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verify installations
docker --version
docker-compose --version

# Install AWS CLI v2 (usually pre-installed on Amazon Linux 2023)
if ! command -v aws &> /dev/null; then
    echo "Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip
fi

aws --version

# Create application directory
echo "Creating application directory..."
mkdir -p /opt/${project_name}
cd /opt/${project_name}

# Fetch secrets from SSM Parameter Store
echo "Fetching secrets from SSM Parameter Store..."
export OPENAI_API_KEY=$(aws ssm get-parameter --name "/${project_name}/openai/api-key" --with-decryption --query "Parameter.Value" --output text --region ${aws_region} || echo "")
export RDS_HOST=$(aws ssm get-parameter --name "/${project_name}/database/host" --with-decryption --query "Parameter.Value" --output text --region ${aws_region})
export RDS_PORT=$(aws ssm get-parameter --name "/${project_name}/database/port" --query "Parameter.Value" --output text --region ${aws_region})
export RDS_DB=$(aws ssm get-parameter --name "/${project_name}/database/name" --query "Parameter.Value" --output text --region ${aws_region})
export RDS_USER=$(aws ssm get-parameter --name "/${project_name}/database/username" --with-decryption --query "Parameter.Value" --output text --region ${aws_region})
export RDS_PASSWORD=$(aws ssm get-parameter --name "/${project_name}/database/password" --with-decryption --query "Parameter.Value" --output text --region ${aws_region})

# Create .env file
echo "Creating .env file..."
cat > .env << EOF
# Database Configuration
RDS_HOST=$RDS_HOST
RDS_PORT=$RDS_PORT
RDS_DB=$RDS_DB
RDS_USER=$RDS_USER
RDS_PASSWORD=$RDS_PASSWORD

# External Services
OPENAI_API_KEY=$OPENAI_API_KEY

# ECR Configuration
ECR_REGISTRY=${ecr_registry}
IMAGE_TAG=latest

# AWS Configuration
AWS_REGION=${aws_region}
AWS_DEFAULT_REGION=${aws_region}
EOF

# Create docker-compose.yml
echo "Creating docker-compose.yml..."
cat > docker-compose.yml << 'EOFDC'
version: '3.8'

services:
  rag-api:
    image: ${ecr_registry}/rag-api:$${IMAGE_TAG:-latest}
    container_name: rag-api
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=$${OPENAI_API_KEY}
      - RDS_HOST=$${RDS_HOST}
      - RDS_DB=$${RDS_DB}
      - RDS_USER=$${RDS_USER}
      - RDS_PASSWORD=$${RDS_PASSWORD}
      - RDS_PORT=$${RDS_PORT:-5432}
    networks:
      - rag-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  chatbot:
    image: ${ecr_registry}/chatbot:$${IMAGE_TAG:-latest}
    container_name: chatbot
    ports:
      - "8501:8501"
    environment:
      - RAG_API_BASE_URL=http://rag-api:8000
      - OPENAI_API_KEY=$${OPENAI_API_KEY}
      - RDS_HOST=$${RDS_HOST}
      - RDS_DB=$${RDS_DB}
      - RDS_USER=$${RDS_USER}
      - RDS_PASSWORD=$${RDS_PASSWORD}
      - RDS_PORT=$${RDS_PORT:-5432}
    networks:
      - rag-network
    restart: unless-stopped
    depends_on:
      rag-api:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  rag-network:
    driver: bridge
EOFDC

# Create deployment script
echo "Creating deployment script..."
cat > deploy.sh << 'EOFSCRIPT'
#!/bin/bash
set -e

echo "=========================================="
echo "Deploying RAG Project"
echo "Date: $(date)"
echo "=========================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${ecr_registry}

# Pull latest images
echo "Pulling latest images..."
docker-compose pull || echo "Warning: Failed to pull some images. They may not exist yet in ECR."

# Start services
echo "Starting services..."
docker-compose up -d

# Show status
echo "Checking service status..."
docker-compose ps

echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
EOFSCRIPT

chmod +x deploy.sh

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/${project_name}.service << EOF
[Unit]
Description=${project_name} RAG Application
After=docker.service
Requires=docker.service
StartLimitIntervalSec=0

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/${project_name}
ExecStart=/opt/${project_name}/deploy.sh
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=300
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
systemctl daemon-reload
systemctl enable ${project_name}.service

# Attempt initial deployment (may fail if ECR is empty)
echo "Attempting initial deployment..."
./deploy.sh || {
    echo "=========================================="
    echo "WARNING: Initial deployment failed."
    echo "This is expected if ECR repositories are empty."
    echo "After pushing images to ECR, you can deploy with:"
    echo "  sudo systemctl start ${project_name}.service"
    echo "Or manually:"
    echo "  cd /opt/${project_name} && ./deploy.sh"
    echo "=========================================="
}

# Set ownership
chown -R ec2-user:ec2-user /opt/${project_name}

echo "=========================================="
echo "User data script completed"
echo "Date: $(date)"
echo "=========================================="

