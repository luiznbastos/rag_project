.PHONY: help build-rag build-chatbot build-all tag-rag tag-chatbot push-rag push-chatbot push-all ecr-login deploy clean

# Variables
AWS_REGION ?= us-east-1
AWS_ACCOUNT_ID ?= $(shell aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
IMAGE_TAG ?= latest
COMMIT_SHA ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "local")

RAG_IMAGE = rag-api
CHATBOT_IMAGE = chatbot

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build-rag: ## Build RAG API Docker image
	@echo "Building RAG API image..."
	docker build -t $(RAG_IMAGE):$(IMAGE_TAG) ./rag

build-chatbot: ## Build Chatbot Docker image
	@echo "Building Chatbot image..."
	docker build -t $(CHATBOT_IMAGE):$(IMAGE_TAG) ./chatbot

build-all: build-rag build-chatbot ## Build all Docker images
	@echo "All images built successfully"

tag-rag: ## Tag RAG image for ECR
	@echo "Tagging RAG API image for ECR..."
	docker tag $(RAG_IMAGE):$(IMAGE_TAG) $(ECR_REGISTRY)/$(RAG_IMAGE):$(IMAGE_TAG)
	docker tag $(RAG_IMAGE):$(IMAGE_TAG) $(ECR_REGISTRY)/$(RAG_IMAGE):$(COMMIT_SHA)

tag-chatbot: ## Tag Chatbot image for ECR
	@echo "Tagging Chatbot image for ECR..."
	docker tag $(CHATBOT_IMAGE):$(IMAGE_TAG) $(ECR_REGISTRY)/$(CHATBOT_IMAGE):$(IMAGE_TAG)
	docker tag $(CHATBOT_IMAGE):$(IMAGE_TAG) $(ECR_REGISTRY)/$(CHATBOT_IMAGE):$(COMMIT_SHA)

tag-all: tag-rag tag-chatbot ## Tag all images for ECR
	@echo "All images tagged successfully"

ecr-login: ## Login to AWS ECR
	@echo "Logging into ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

push-rag: ## Push RAG image to ECR
	@echo "Pushing RAG API image to ECR..."
	docker push $(ECR_REGISTRY)/$(RAG_IMAGE):$(IMAGE_TAG)
	docker push $(ECR_REGISTRY)/$(RAG_IMAGE):$(COMMIT_SHA)

push-chatbot: ## Push Chatbot image to ECR
	@echo "Pushing Chatbot image to ECR..."
	docker push $(ECR_REGISTRY)/$(CHATBOT_IMAGE):$(IMAGE_TAG)
	docker push $(ECR_REGISTRY)/$(CHATBOT_IMAGE):$(COMMIT_SHA)

push-all: push-rag push-chatbot ## Push all images to ECR
	@echo "All images pushed successfully"

deploy: ecr-login build-all tag-all push-all ## Complete deployment workflow (login, build, tag, push)
	@echo "Deployment complete!"
	@echo "RAG API: $(ECR_REGISTRY)/$(RAG_IMAGE):$(IMAGE_TAG)"
	@echo "Chatbot: $(ECR_REGISTRY)/$(CHATBOT_IMAGE):$(IMAGE_TAG)"

clean: ## Remove local Docker images
	@echo "Cleaning up local images..."
	docker rmi -f $(RAG_IMAGE):$(IMAGE_TAG) $(CHATBOT_IMAGE):$(IMAGE_TAG) 2>/dev/null || true
	docker rmi -f $(ECR_REGISTRY)/$(RAG_IMAGE):$(IMAGE_TAG) $(ECR_REGISTRY)/$(CHATBOT_IMAGE):$(IMAGE_TAG) 2>/dev/null || true
	@echo "Cleanup complete"

