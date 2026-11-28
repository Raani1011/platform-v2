#!/usr/bin/env bash
# Run after `terraform apply`. Sets up secrets, the database and ArgoCD in one go.
set -euo pipefail
cd "$(dirname "$0")/.."

TF="terraform -chdir=terraform"
REGION=ap-south-1
ESO_VERSION=2.15.0
CLUSTER=$($TF output -raw cluster_name)

echo ">> 1/6 Connecting kubectl to $CLUSTER"
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER"

echo ">> 2/6 Installing External Secrets Operator"
# Download the chart with retries (Helm's own GitHub download sometimes times out)
if [ ! -f /tmp/eso-chart.tgz ]; then
  curl -fL --retry 5 --retry-delay 3 --connect-timeout 20 -o /tmp/eso-chart.tgz \
    "https://github.com/external-secrets/external-secrets/releases/download/helm-chart-${ESO_VERSION}/external-secrets-${ESO_VERSION}.tgz"
fi
helm upgrade --install external-secrets /tmp/eso-chart.tgz \
  -n external-secrets --create-namespace \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="$($TF output -raw eso_role_arn)" \
  --wait --timeout 5m

echo ">> 3/6 Syncing secrets from AWS Secrets Manager"
kubectl create namespace platform --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f gitops/secrets/cluster-secret-store.yaml
export RDS_SECRET_ARN=$($TF output -raw rds_master_secret_arn)
envsubst < gitops/secrets/external-secrets.yaml | kubectl apply -f -
kubectl wait --for=condition=Ready externalsecret/db-credentials externalsecret/jwt-secret -n platform --timeout=120s

echo ">> 4/6 Creating notes_db on RDS"
export RDS_HOST=$($TF output -raw rds_endpoint)
kubectl delete job create-notes-db -n platform --ignore-not-found
envsubst < gitops/jobs/create-notes-db.yaml | kubectl apply -f -
kubectl wait --for=condition=complete job/create-notes-db -n platform --timeout=180s

echo ">> 5/6 Installing ArgoCD"
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd --server-side --force-conflicts \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=available deployment --all -n argocd --timeout=300s

echo ">> 6/6 Handing ArgoCD the root app (app-of-apps)"
kubectl apply -f gitops/argocd/root-app.yaml

echo ""
echo "Bootstrap complete. DB host check (these two must match):"
echo "  Terraform output : $RDS_HOST"
echo "  Values file      : $(grep DB_HOST gitops/values/users-service.yaml | awk '{print $2}')"
