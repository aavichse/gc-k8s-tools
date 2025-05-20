resource "aws_eks_cluster" "gc_eks" {
  name     = "gc-k8s-eks-${var.instance}"
  role_arn = var.eks_cluster_role_arn
  version  = var.eks_cluster_version

  vpc_config {
    subnet_ids = [
      aws_subnet.gc_subnet_a.id,
      aws_subnet.gc_subnet_b.id
    ]
  }

  tags = {
    owner = var.owner
    team  = var.team
  }
}

# resource "aws_launch_template" "gc_ng_template" {
#   name_prefix   = "gc-k8s-${var.instance}-ng-template"
#   image_id      = var.node_ami_id           
#   instance_type = var.node_instance_type            

#   tag_specifications {
#     resource_type = "instance"
#     tags = {
#       Name  = "gc-k8s-node-${var.instance}"
#       owner = var.owner
#       team  = var.team
#     }
#   }
# }

resource "aws_eks_node_group" "gc_ng" {
  cluster_name    = aws_eks_cluster.gc_eks.name
  node_group_name = "gc-k8s-${var.instance}-ng"
  node_role_arn   = var.eks_node_role_arn
  subnet_ids      = [aws_subnet.gc_subnet_a.id, aws_subnet.gc_subnet_b.id]

#   launch_template {
#     id      = aws_launch_template.gc_ng_template.id
#     version = "$Latest"
#   }

  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 1
  }

  tags = {
    Name  = "gc-k8s-${var.instance}-nodes"
    owner = var.owner
    team  = var.team
  }
}

