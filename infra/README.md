# CONCORD Infrastructure & DevOps

This directory contains the Infrastructure as Code (IaC) and Orchestration logic for the CONCORD project.

## 1. CI/CD Pipelines (`.github/workflows`)
*   **`polyglot-ci.yml`**: Runs parallel tests for Rust, Python, Java, C++, and R. Includes Trivy security scanning.
*   **`docker-publish.yml`**: Builds and pushes Docker images to GHCR.

## 2. Infrastructure as Code (`infra/terraform`)
We use Terraform to provision the AWS cloud environment.
*   **VPC**: Public/Private subnets across 2 AZs.
*   **EKS**: Kubernetes Cluster (Control Plane + Worker Nodes).
*   **RDS**: Managed PostgreSQL database.

### Usage
```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

## 3. Orchestration (`infra/charts`)
We use Helm to package and deploy the microservices.

### Install
```bash
helm install concord infra/charts/concord --namespace concord --create-namespace
```

### Configuration
Update `infra/charts/concord/values.yaml` to configure resource limits, replica counts, and image tags.

## 4. DevSecOps
*   **Scanning**: Container images are scanned by Trivy in the CI pipeline.
*   **Observability**: Prometheus `ServiceMonitor` resources are included in the Helm chart for metrics scraping.
