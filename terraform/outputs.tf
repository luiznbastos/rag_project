# Application Access
output "ec2_public_ip" {
  description = "Public IP of the EC2 instance (use this to access applications)"
  value       = aws_instance.app_server.public_ip
}

output "chatbot_url" {
  description = "URL for the Chatbot UI"
  value       = "http://${aws_instance.app_server.public_ip}:8501"
}

output "rag_api_url" {
  description = "URL for the RAG API"
  value       = "http://${aws_instance.app_server.public_ip}:8000"
}

# Database
output "rds_endpoint" {
  description = "RDS instance endpoint (for database connections)"
  value       = aws_db_instance.main.endpoint
}

# ECR (for deployment)
output "ecr_registry" {
  description = "ECR registry URL (for docker login and image push)"
  value       = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

