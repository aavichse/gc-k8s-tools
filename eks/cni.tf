resource "aws_eks_addon" "aws_cni" {
  cluster_name = "gc-k8s-eks-${var.instance}"
  addon_name   = "vpc-cni"
  addon_version = "v1.19.6-eksbuild.1" 

  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "PRESERVE"

  configuration_values = jsonencode({
    enableNetworkPolicy = "true"
    nodeAgent = {
      enablePolicyEventLogs = "true"
    }
  })

  # Optional: use a specific IAM role for the addon’s service account
  # service_account_role_arn = aws_iam_role.cni_sa_role.arn
  
  tags = {
    managed_by = "terraform"
  }
}
