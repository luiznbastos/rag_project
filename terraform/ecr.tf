# ECR Repository for RAG API
resource "aws_ecr_repository" "rag_api" {
  name                 = "rag-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name        = "${var.project_name}-rag-api"
    Description = "Docker images for RAG API service"
  }
}

# Lifecycle policy for RAG API repository
resource "aws_ecr_lifecycle_policy" "rag_api" {
  repository = aws_ecr_repository.rag_api.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 tagged images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Remove untagged images after 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ECR Repository for Chatbot
resource "aws_ecr_repository" "chatbot" {
  name                 = "chatbot"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name        = "${var.project_name}-chatbot"
    Description = "Docker images for Chatbot service"
  }
}

# Lifecycle policy for Chatbot repository
resource "aws_ecr_lifecycle_policy" "chatbot" {
  repository = aws_ecr_repository.chatbot.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 tagged images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Remove untagged images after 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# SSM Parameters for ECR URLs
resource "aws_ssm_parameter" "ecr_rag_api_url" {
  name        = "/${var.project_name}/ecr/rag-api/url"
  description = "ECR repository URL for RAG API"
  type        = "String"
  value       = aws_ecr_repository.rag_api.repository_url

  tags = {
    Name = "${var.project_name}-ecr-rag-api-url"
  }
}

resource "aws_ssm_parameter" "ecr_chatbot_url" {
  name        = "/${var.project_name}/ecr/chatbot/url"
  description = "ECR repository URL for Chatbot"
  type        = "String"
  value       = aws_ecr_repository.chatbot.repository_url

  tags = {
    Name = "${var.project_name}-ecr-chatbot-url"
  }
}

