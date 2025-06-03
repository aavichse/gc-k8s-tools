
variable "instance" {
  description = "Unique identifier postfix for all resource names"
  type        = string
  default     = "arika"
}

variable "owner" {
  description = "Owner tag for resources"
  type        = string
  default     = "arika"
}

variable "team" {
  description = "Team tag for resources"
  type        = string
  default     = "k8s"
}

variable "subnet_a" {
  description = "subnet a"
  type        = string
  default     = "10.0.0.0/24"
}


variable "subnet_b" {
  description = "subnet b"
  type        = string
  default     = "10.0.1.0/24"
}

# Example of query for the recommended Amazon 2023 standard ami 
#
# aws ssm get-parameter \
#  --name /aws/service/eks/optimized-ami/1.29/amazon-linux-2023/x86_64/standard/recommended/image_id \
#  --region "eu-central-1" \
#  --query "Parameter.Value" \
#  --output text
#
variable "node_ami_id" {
  description = "AMI ID for EKS worker nodes"
  type        = string
  default     = "ami-0e056134cbc299dd2"
}

variable "node_instance_type" {
  description = "workernode instance type"
  type        = string
  default     = "t3.medium"
}

variable "eks_cluster_role_arn" {
  description = "Existing IAM role ARN for EKS"
  type        = string
  default     = "arn:aws:iam::324264561773:role/k8s-team-role"
}

variable "eks_node_role_arn" {
  description = "Existing IAM role ARN for EKS control plane"
  type        = string
  default     = "arn:aws:iam::324264561773:role/k8s-team-role-1"
}

variable "eks_cluster_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.29"
}