resource "null_resource" "remove_aws_cni" {
  provisioner "local-exec" {
    command = "kubectl delete daemonset aws-node -n kube-system || true"
  }

  depends_on = [aws_eks_node_group.gc_ng]
}

provider "helm" {
  kubernetes {
    host                   = aws_eks_cluster.gc_eks.endpoint
    cluster_ca_certificate = base64decode(aws_eks_cluster.gc_eks.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

resource "helm_release" "tigera_operator" {
  name       = "tigera-operator"
  namespace  = "tigera-operator"
  chart      = "tigera-operator"
  repository = "https://projectcalico.docs.tigera.io/charts"
  version    = "v3.28.0"  # Or latest compatible

  create_namespace = true

  values = [
    yamlencode({
      installation = {
        kubernetesProvider = "EKS"
        cni = {
          type = "Calico"
        }
      }
      apiServer = {
        enabled = true
      }
    })
  ]
}
