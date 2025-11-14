# Security Group for EC2 Instance
resource "aws_security_group" "ec2" {
  name        = "${var.project_name}-ec2-sg"
  description = "Security group for EC2 instance hosting RAG application"
  vpc_id      = data.aws_vpc.default.id

  # Allow HTTP (port 80) from anywhere
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTPS (port 443) from anywhere
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow RAG API (port 8000) from anywhere
  ingress {
    description = "RAG API from anywhere"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow Chatbot (port 8501) from anywhere
  ingress {
    description = "Chatbot from anywhere"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow SSH from developer IP
  ingress {
    description = "SSH from developer"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.developer_ip]
  }

  # Allow all outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ec2-sg"
  }
}

# EC2 Instance
resource "aws_instance" "app_server" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  subnet_id              = data.aws_subnets.default.ids[0]

  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    aws_region       = var.aws_region
    project_name     = var.project_name
    ecr_registry     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
    rag_api_repo_url = aws_ecr_repository.rag_api.repository_url
    chatbot_repo_url = aws_ecr_repository.chatbot.repository_url
  }))

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  tags = {
    Name = "${var.project_name}-app-server"
  }

  depends_on = [
    aws_ecr_repository.rag_api,
    aws_ecr_repository.chatbot,
    aws_db_instance.main
  ]
}

