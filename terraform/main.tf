terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1" # Tokyo
}

# Get current public IP address
data "http" "my_ip" {
  url = "https://checkip.amazonaws.com"
}

locals {
  my_ip = chomp(data.http.my_ip.response_body)
}

# Generate SSH key pair
resource "tls_private_key" "ec2_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Create AWS key pair
resource "aws_key_pair" "polymarket" {
  key_name   = "polymarket-ec2-key"
  public_key = tls_private_key.ec2_key.public_key_openssh
}

# Save private key to local file
resource "local_file" "private_key" {
  content         = tls_private_key.ec2_key.private_key_pem
  filename        = "${path.module}/polymarket-ec2-key.pem"
  file_permission = "0400"
}

# Get latest Ubuntu 22.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Security group
resource "aws_security_group" "polymarket_postgres" {
  name        = "polymarket_postgres_sg"
  description = "Security group for Polymarket PostgreSQL EC2 instance"

  # SSH access from local IP only
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${local.my_ip}/32"]
    description = "SSH from local IP"
  }

  # PostgreSQL access from local IP only
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["${local.my_ip}/32"]
    description = "PostgreSQL from local IP"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name = "polymarket-postgres-sg"
  }
}

# EC2 instance
resource "aws_instance" "polymarket_postgres" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  key_name      = aws_key_pair.polymarket.key_name

  vpc_security_group_ids = [aws_security_group.polymarket_postgres.id]

  user_data = <<-EOF
              #!/bin/bash
              set -e

              # Update system
              apt-get update
              apt-get upgrade -y

              # Install Docker
              apt-get install -y ca-certificates curl gnupg
              install -m 0755 -d /etc/apt/keyrings
              curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
              chmod a+r /etc/apt/keyrings/docker.gpg

              echo \
                "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
                $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
                tee /etc/apt/sources.list.d/docker.list > /dev/null

              apt-get update
              apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

              # Start Docker service
              systemctl start docker
              systemctl enable docker

              # Create docker-compose.yml for PostgreSQL
              mkdir -p /opt/polymarket
              cat > /opt/polymarket/docker-compose.yml <<'COMPOSE'
              version: '3.8'
              services:
                postgres:
                  image: postgres:16-alpine
                  container_name: polymarket_postgres
                  environment:
                    POSTGRES_DB: polymarket_data
                    POSTGRES_USER: polymarket
                    POSTGRES_PASSWORD: ${var.database_password}
                  ports:
                    - "5432:5432"
                  volumes:
                    - postgres_data:/var/lib/postgresql/data
                  restart: unless-stopped

              volumes:
                postgres_data:
              COMPOSE

              # Start PostgreSQL container
              cd /opt/polymarket
              docker compose up -d

              # Ensure PostgreSQL starts on boot
              cat > /etc/systemd/system/polymarket-postgres.service <<'SERVICE'
              [Unit]
              Description=Polymarket PostgreSQL Container
              Requires=docker.service
              After=docker.service

              [Service]
              Type=oneshot
              RemainAfterExit=yes
              WorkingDirectory=/opt/polymarket
              ExecStart=/usr/bin/docker compose up -d
              ExecStop=/usr/bin/docker compose down

              [Install]
              WantedBy=multi-user.target
              SERVICE

              systemctl enable polymarket-postgres.service
              EOF

  tags = {
    Name = "polymarket-postgres"
  }

  # Ensure instance has a public IP
  associate_public_ip_address = true
}
