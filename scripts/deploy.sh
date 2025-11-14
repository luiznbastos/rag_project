#!/bin/bash
set -e

# RAG Project Deployment Script
# This script builds, pushes images to ECR, and optionally deploys to EC2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
EC2_HOST=${EC2_HOST:-}
EC2_USER=${EC2_USER:-ec2-user}
SSH_KEY=${SSH_KEY:-~/.ssh/rag-project-key.pem}

echo -e "${GREEN}=== RAG Project Deployment ===${NC}"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not configured properly${NC}"
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo -e "${GREEN}✓${NC} AWS Account: ${AWS_ACCOUNT_ID}"
echo -e "${GREEN}✓${NC} ECR Registry: ${ECR_REGISTRY}"
echo ""

# Build and push images using Makefile
echo -e "${YELLOW}Building and pushing Docker images...${NC}"
make deploy AWS_REGION=${AWS_REGION}

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to build and push images${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Images successfully pushed to ECR"
echo ""

# Deploy to EC2 if host is provided
if [ -n "$EC2_HOST" ]; then
    echo -e "${YELLOW}Deploying to EC2: ${EC2_HOST}${NC}"
    
    if [ ! -f "$SSH_KEY" ]; then
        echo -e "${RED}ERROR: SSH key not found: ${SSH_KEY}${NC}"
        echo "Set SSH_KEY environment variable or place key at default location"
        exit 1
    fi
    
    # SSH to EC2 and deploy
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${EC2_USER}@${EC2_HOST}" << EOF
set -e

echo "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_REGISTRY}

cd /opt/rag-project

echo "Pulling latest images..."
docker-compose pull

echo "Restarting services..."
docker-compose up -d --force-recreate

echo "Checking service status..."
docker-compose ps

echo "Deployment complete!"
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Successfully deployed to EC2"
        echo ""
        echo -e "Access points:"
        echo -e "  Chatbot:  http://${EC2_HOST}:8501"
        echo -e "  RAG API:  http://${EC2_HOST}:8000/docs"
    else
        echo -e "${RED}ERROR: Deployment to EC2 failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC}  EC2_HOST not set, skipping EC2 deployment"
    echo ""
    echo "To deploy to EC2, set environment variables:"
    echo "  export EC2_HOST=<your-ec2-ip>"
    echo "  export SSH_KEY=<path-to-ssh-key>"
    echo "  ./scripts/deploy.sh"
fi

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"

