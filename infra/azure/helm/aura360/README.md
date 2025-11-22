# AURA360 - Helm Chart Deployment Guide

This Helm chart deploys the complete AURA360 holistic wellness platform on Azure Kubernetes Service (AKS).

## Prerequisites

1. **Azure CLI** - Authenticated and connected to your subscription
2. **kubectl** - Configured to connect to your AKS cluster
3. **Helm 3.x** - Installed on your local machine
4. **AKS Cluster** - Running and accessible (created via Terraform in `infra/azure/terraform/`)
5. **Container Images** - Built and pushed to ACR (aura360prodacr.azurecr.io)

## Architecture

The chart deploys:

### Infrastructure Components
- **Qdrant** - Vector database (with Azure Files persistence)
- **Redis** - Cache and message broker (with Azure Files persistence)
- **GROBID** - PDF processing service

### Application Components
- **API** - Django REST API (Supabase-backed)
- **Agents** - FastAPI agents service (Google ADK)
- **VectorDB API** - FastAPI vector ingestion API
- **VectorDB Worker** - Celery worker for async processing
- **Web** - Angular SSR frontend

### Networking
- **Ingress** - NGINX Ingress Controller
- **Services** - ClusterIP for internal communication

## Quick Start

### 1. Connect to AKS Cluster

```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group aura360-prod-rg \
  --name aura360-prod-aks \
  --overwrite-existing

# Verify connection
kubectl get nodes
```

### 2. Install NGINX Ingress Controller

```bash
# Add Helm repo
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install NGINX Ingress
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz
```

### 3. Configure Secrets

**IMPORTANT**: Before deploying, update secrets with your actual credentials.

```bash
# Create Supabase credentials secret
kubectl create secret generic supabase-credentials \
  --namespace aura360 \
  --from-literal=url='https://your-project.supabase.co' \
  --from-literal=service_role_key='your-service-role-key' \
  --from-literal=jwt_secret='your-jwt-secret' \
  --from-literal=anon_key='your-anon-key' \
  --dry-run=client -o yaml | kubectl apply -f -

# Create Google API credentials secret
kubectl create secret generic google-api-credentials \
  --namespace aura360 \
  --from-literal=api_key='your-google-api-key' \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 4. Deploy AURA360 (Development)

```bash
# From project root
cd infra/azure/helm/aura360

# Deploy with dev values
helm install aura360 . \
  --namespace aura360 \
  --create-namespace \
  --values values.yaml \
  --values values-dev.yaml
```

### 5. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n aura360

# Check services
kubectl get svc -n aura360

# Check ingress
kubectl get ingress -n aura360

# Get external IP of nginx-ingress
kubectl get svc -n ingress-nginx
```

### 6. Access the Application

Get the LoadBalancer external IP:

```bash
EXTERNAL_IP=$(kubectl get svc nginx-ingress-ingress-nginx-controller \
  -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "External IP: $EXTERNAL_IP"
```

Add to your `/etc/hosts` (for local testing):

```
<EXTERNAL_IP>  aura360-dev.eastus2.cloudapp.azure.com
<EXTERNAL_IP>  api-dev.eastus2.cloudapp.azure.com
<EXTERNAL_IP>  agents-dev.eastus2.cloudapp.azure.com
```

Access URLs:
- **Web**: http://aura360-dev.eastus2.cloudapp.azure.com
- **API**: http://api-dev.eastus2.cloudapp.azure.com/api/v1/
- **Agents**: http://agents-dev.eastus2.cloudapp.azure.com/readyz

## Production Deployment

For production, use custom domain names and enable TLS:

```bash
# Deploy with production values
helm install aura360 . \
  --namespace aura360 \
  --create-namespace \
  --values values.yaml \
  --values values-prod.yaml
```

### Enable TLS with cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@aura360.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Upgrading

```bash
# Upgrade to new version
helm upgrade aura360 . \
  --namespace aura360 \
  --values values.yaml \
  --values values-dev.yaml
```

## Uninstalling

```bash
# Delete the release
helm uninstall aura360 --namespace aura360

# Delete the namespace (optional)
kubectl delete namespace aura360
```

## Configuration

### Key Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.domain` | Base domain for ingress | `aura360.local` |
| `global.environment` | Environment label | `development` |
| `global.storageClass` | Storage class for PVCs | `azurefile-premium` |
| `namespaceCreate` | Whether Helm should create the namespace | `false` |
| `storage.createCustomClasses` | Create azurefile/azurefile-premium storage classes | `false` |
| `imageRegistry` | ACR registry URL | `aura360prodacr.azurecr.io` |
| `api.replicas` | API pod replicas | `2` |
| `qdrant.persistence.size` | Qdrant storage size | `10Gi` |

See `values.yaml` for all configuration options.

### Environment-Specific Values

- **values-dev.yaml** - Development/testing (reduced resources, no autoscaling)
- **values-prod.yaml** - Production (TLS enabled, higher resources)

## Troubleshooting

### Check Pod Logs

```bash
# API logs
kubectl logs -n aura360 -l app.kubernetes.io/component=api --tail=100 -f

# Agents logs
kubectl logs -n aura360 -l app.kubernetes.io/component=agents --tail=100 -f

# Qdrant logs
kubectl logs -n aura360 -l app.kubernetes.io/component=qdrant --tail=100 -f
```

### Check Pod Status

```bash
# Describe pod for detailed info
kubectl describe pod <pod-name> -n aura360

# Get events
kubectl get events -n aura360 --sort-by='.lastTimestamp'
```

### Storage Issues

```bash
# Check PVCs
kubectl get pvc -n aura360

# Check PVs
kubectl get pv

# Describe PVC
kubectl describe pvc qdrant-storage -n aura360
```

### Ingress Issues

```bash
# Check ingress details
kubectl describe ingress aura360-ingress -n aura360

# Check nginx-ingress logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

## Monitoring

### Resource Usage

```bash
# Top nodes
kubectl top nodes

# Top pods
kubectl top pods -n aura360
```

### Health Checks

```bash
# API health
curl http://api-dev.eastus2.cloudapp.azure.com/api/v1/health

# Agents health
curl http://agents-dev.eastus2.cloudapp.azure.com/readyz

# VectorDB health
curl http://vectordb.aura360.local:8001/readyz
```

## Next Steps

1. **Configure DNS** - Point your domain to the LoadBalancer IP
2. **Enable TLS** - Install cert-manager and configure certificates
3. **Set up monitoring** - Deploy Prometheus + Grafana
4. **Configure backups** - Set up Azure Backup for PVCs
5. **CI/CD** - Automate deployments with GitHub Actions or Azure DevOps

## Support

For issues or questions:
- Check the [main README](../../../../README.md)
- Review [CLAUDE.md](../../../../docs/runbooks/agents/CLAUDE.md) for project documentation
- Open an issue in the project repository
