variable "aws_region" {
  description = "The AWS region to deploy to"
  default     = "eu-central-1"
}

variable "instance_type" {
  description = "The EC2 instance type"
  default     = "t3.medium" # 2 vCPU, 4GB RAM is recommended for Pandas/Polars + Celery
}

variable "ssh_key_name" {
  description = "The name of the SSH key pair to use for EC2 access"
  type        = string
}
