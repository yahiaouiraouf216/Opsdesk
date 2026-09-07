output "vpc_id" {
  description = "ID of the OpsDesk VPC"
  value       = aws_vpc.opsdesk_vpc.id
}

output "subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.opsdesk_subnet.id
}

output "security_group_id" {
  description = "ID of the OpsDesk security group"
  value       = aws_security_group.opsdesk_sg.id
}

output "instance_id" {
  description = "ID of the OpsDesk EC2 instance"
  value       = aws_instance.opsdesk_instance.id
}

output "instance_public_ip" {
  description = "Public IP address of the OpsDesk EC2 instance"
  value       = aws_instance.opsdesk_instance.public_ip
}