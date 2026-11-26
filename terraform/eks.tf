module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = local.cluster_name
  cluster_version = var.kubernetes_version

  cluster_endpoint_public_access           = true
  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Cost savers: no control-plane logs, no extra KMS key
  cluster_enabled_log_types   = []
  create_cloudwatch_log_group = false
  create_kms_key              = false
  cluster_encryption_config   = {}

  cluster_addons = {
    coredns    = {}
    kube-proxy = {}
    vpc-cni    = { before_compute = true }
  }

  eks_managed_node_groups = {
    spot = {
      ami_type       = "AL2023_x86_64_STANDARD"
      capacity_type  = "SPOT"
      instance_types = ["t3.medium", "t3a.medium"]

      min_size     = 1
      max_size     = 3
      desired_size = 2
    }
  }
}
