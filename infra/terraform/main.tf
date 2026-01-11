provider "aws" {
  region = "us-east-1"
}

module "vpc" {
  source      = "./modules/vpc"
  environment = "concord-prod"
  vpc_cidr    = "10.0.0.0/16"
}

module "eks" {
  source       = "./modules/eks"
  cluster_name = "concord-cluster"
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnets
}

module "rds" {
  source      = "./modules/rds"
  db_name     = "concord_db"
  db_username = "admin"
  db_password = "ChangeMe123!" # In production, use Secrets Manager!
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
}

# Outputs needed for K8s config
output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_name" {
  value = module.eks.cluster_name
}
