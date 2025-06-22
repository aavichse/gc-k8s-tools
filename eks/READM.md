
## Installation
To complete the installation by `terraform`, we should import auth config map and re-apply terraform:
```bash
$ terraform import kubernetes_config_map.aws_auth kube-system/aws-auth
$ terraform apply
```

## Import kubeconfig 
```bash
aws eks update-kubeconfig  --region eu-central-1 --name gc-k8s-eks-arika
``

## View used resources
Example of resources by tag `owner=arika`
```bash
aws resourcegroupstaggingapi get-resources   \
    --tag-filters Key=owner,Values=arika   \
    --region eu-central-1   \
    --query 'ResourceTagMappingList[*].[ResourceARN, Tags[?Key==`Name`].Value | [0]]'\
    --output table
```
