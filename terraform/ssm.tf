# SSM Parameters for Database Credentials
resource "aws_ssm_parameter" "db_host" {
  name        = "/${var.project_name}/database/host"
  description = "Database host endpoint"
  type        = "SecureString"
  value       = aws_db_instance.main.address

  tags = {
    Name = "${var.project_name}-db-host"
  }
}

resource "aws_ssm_parameter" "db_port" {
  name        = "/${var.project_name}/database/port"
  description = "Database port"
  type        = "String"
  value       = tostring(var.db_port)

  tags = {
    Name = "${var.project_name}-db-port"
  }
}

resource "aws_ssm_parameter" "db_name" {
  name        = "/${var.project_name}/database/name"
  description = "Database name"
  type        = "String"
  value       = var.db_name

  tags = {
    Name = "${var.project_name}-db-name"
  }
}

resource "aws_ssm_parameter" "db_username" {
  name        = "/${var.project_name}/database/username"
  description = "Database username"
  type        = "SecureString"
  value       = var.db_username

  tags = {
    Name = "${var.project_name}-db-username"
  }
}

resource "aws_ssm_parameter" "db_password" {
  name        = "/${var.project_name}/database/password"
  description = "Database password"
  type        = "SecureString"
  value       = random_password.db_password.result

  tags = {
    Name = "${var.project_name}-db-password"
  }
}

# Placeholder SSM Parameters for external services
# These should be set manually after infrastructure creation

resource "aws_ssm_parameter" "openai_api_key" {
  name        = "/${var.project_name}/openai/api-key"
  description = "OpenAI API key (set this manually)"
  type        = "SecureString"
  value       = "REPLACE_ME"

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    Name = "${var.project_name}-openai-key"
  }
}


