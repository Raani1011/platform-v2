output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "rds_master_secret_arn" {
  value = aws_db_instance.postgres.master_user_secret[0].secret_arn
}

output "configure_kubectl" {
  value = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}

output "eso_role_arn" {
  value = module.eso_irsa.iam_role_arn
}

output "jwt_secret_name" {
  value = aws_secretsmanager_secret.jwt.name
}
