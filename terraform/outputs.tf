output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.polymarket_postgres.public_ip
}

output "database_url" {
  description = "PostgreSQL connection string"
  value       = "postgresql://polymarket:${var.database_password}@${aws_instance.polymarket_postgres.public_ip}:5432/polymarket_data"
  sensitive   = true
}

output "ssh_private_key_path" {
  description = "Path to the SSH private key file"
  value       = local_file.private_key.filename
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ${local_file.private_key.filename} ubuntu@${aws_instance.polymarket_postgres.public_ip}"
}

output "your_current_ip" {
  description = "Your current public IP address (used in security group)"
  value       = local.my_ip
}
