output "server_public_ip" {
  description = "The public IP address of the DataSense production server"
  value       = aws_instance.datasense_server.public_ip
}

output "server_ssh_command" {
  description = "Command to SSH into the server"
  value       = "ssh -i <your-key.pem> ubuntu@${aws_instance.datasense_server.public_ip}"
}
