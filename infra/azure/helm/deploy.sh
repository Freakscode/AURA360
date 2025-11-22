#!/bin/bash
# AURA360 - Automated Deployment Script for Azure AKS
# This script deploys the complete AURA360 platform to AKS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NAMESPACE=${NAMESPACE:-"aura360"}
CHART_PATH="${SCRIPT_DIR}/aura360"
RELEASE_NAME="aura360"
ENVIRONMENT="${1:-dev}"  # dev, stg o prod
AKS_RESOURCE_GROUP=${AKS_RESOURCE_GROUP:-"aura360-${ENVIRONMENT}-rg"}
AKS_CLUSTER_NAME=${AKS_CLUSTER_NAME:-"aura360-${ENVIRONMENT}-aks"}
AZ_LOCATION=${AZ_LOCATION:-"eastus2"}
DEFAULT_DOMAIN=${DEFAULT_DOMAIN:-"aura360-${ENVIRONMENT}.${AZ_LOCATION}.cloudapp.azure.com"}
API_DOMAIN=${API_DOMAIN:-"api-${ENVIRONMENT}.${AZ_LOCATION}.cloudapp.azure.com"}
AGENTS_DOMAIN=${AGENTS_DOMAIN:-"agents-${ENVIRONMENT}.${AZ_LOCATION}.cloudapp.azure.com"}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AURA360 - Azure AKS Deployment${NC}"
echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}kubectl is required but not installed. Aborting.${NC}" >&2; exit 1; }
command -v helm >/dev/null 2>&1 || { echo -e "${RED}helm is required but not installed. Aborting.${NC}" >&2; exit 1; }
command -v az >/dev/null 2>&1 || { echo -e "${RED}Azure CLI is required but not installed. Aborting.${NC}" >&2; exit 1; }

echo -e "${GREEN}✓ Prerequisites check passed${NC}"

# Verify AKS connection
echo -e "\n${YELLOW}Verifying AKS connection...${NC}"
if ! kubectl get nodes > /dev/null 2>&1; then
    echo -e "${YELLOW}Attempting to download credentials for ${AKS_CLUSTER_NAME}...${NC}"
    if az aks get-credentials --resource-group "${AKS_RESOURCE_GROUP}" --name "${AKS_CLUSTER_NAME}" --overwrite-existing >/dev/null; then
      kubectl get nodes > /dev/null 2>&1 || {
        echo -e "${RED}Still unable to reach AKS. Verifica tu sesión de az login y permisos.${NC}";
        exit 1;
      }
    else
      echo -e "${RED}Cannot connect to AKS cluster automatically. Please run:${NC}"
      echo -e "${YELLOW}  az aks get-credentials --resource-group ${AKS_RESOURCE_GROUP} --name ${AKS_CLUSTER_NAME}${NC}"
      exit 1
    fi
fi
echo -e "${GREEN}✓ Connected to AKS cluster${NC}"

# Install NGINX Ingress Controller if not exists
echo -e "\n${YELLOW}Checking NGINX Ingress Controller...${NC}"
if ! helm list -n ingress-nginx | grep -q nginx-ingress; then
    echo -e "${YELLOW}Installing NGINX Ingress Controller...${NC}"
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update

    helm install nginx-ingress ingress-nginx/ingress-nginx \
      --namespace ingress-nginx \
      --create-namespace \
      --set controller.service.type=LoadBalancer \
      --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz \
      --wait

    echo -e "${GREEN}✓ NGINX Ingress Controller installed${NC}"
else
    echo -e "${GREEN}✓ NGINX Ingress Controller already installed${NC}"
fi

# Configure secrets
echo -e "\n${YELLOW}Configuring secrets...${NC}"
echo -e "${RED}IMPORTANT: Update these with your actual credentials!${NC}"

# Check if secrets exist
if ! kubectl get secret supabase-credentials -n ${NAMESPACE} > /dev/null 2>&1; then
    echo -e "${YELLOW}Creating placeholder Supabase credentials...${NC}"
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    kubectl create secret generic supabase-credentials \
      --namespace ${NAMESPACE} \
      --from-literal=url='https://your-project.supabase.co' \
      --from-literal=service_role_key='your-service-role-key-replace-this' \
      --from-literal=jwt_secret='your-jwt-secret-replace-this' \
      --from-literal=anon_key='your-anon-key-replace-this' \
      --dry-run=client -o yaml | kubectl apply -f -

    echo -e "${RED}⚠ WARNING: Supabase credentials are placeholders. Update them before production!${NC}"
else
    echo -e "${GREEN}✓ Supabase credentials already exist${NC}"
fi

if ! kubectl get secret google-api-credentials -n ${NAMESPACE} > /dev/null 2>&1; then
    echo -e "${YELLOW}Creating placeholder Google API credentials...${NC}"
    kubectl create secret generic google-api-credentials \
      --namespace ${NAMESPACE} \
      --from-literal=api_key='your-google-api-key-replace-this' \
      --dry-run=client -o yaml | kubectl apply -f -

    echo -e "${RED}⚠ WARNING: Google API credentials are placeholders. Update them before production!${NC}"
else
    echo -e "${GREEN}✓ Google API credentials already exist${NC}"
fi

if ! kubectl get secret database-credentials -n ${NAMESPACE} > /dev/null 2>&1; then
    echo -e "${YELLOW}Creating placeholder database credentials...${NC}"
    kubectl create secret generic database-credentials \
      --namespace ${NAMESPACE} \
      --from-literal=host='aws-0-us-east-1.pooler.supabase.com' \
      --from-literal=port='6543' \
      --from-literal=name='postgres' \
      --from-literal=user='postgres' \
      --from-literal=password='replace-me-with-strong-secret' \
      --from-literal=engine='django.db.backends.postgresql' \
      --dry-run=client -o yaml | kubectl apply -f -

    echo -e "${RED}⚠ WARNING: Database credentials are placeholders. Update them before production!${NC}"
else
    echo -e "${GREEN}✓ Database credentials already exist${NC}"
fi

# Deploy AURA360
echo -e "\n${YELLOW}Deploying AURA360 to AKS...${NC}"

VALUES_FILE="values-${ENVIRONMENT}.yaml"
if [ ! -f "${CHART_PATH}/${VALUES_FILE}" ]; then
    echo -e "${RED}Values file ${VALUES_FILE} not found!${NC}"
    exit 1
fi

helm upgrade --install ${RELEASE_NAME} "${CHART_PATH}" \
  --namespace ${NAMESPACE} \
  --create-namespace \
  --values "${CHART_PATH}/values.yaml" \
  --values "${CHART_PATH}/${VALUES_FILE}" \
  --wait \
  --timeout 10m

echo -e "${GREEN}✓ AURA360 deployed successfully!${NC}"

# Get status
echo -e "\n${YELLOW}Deployment Status:${NC}"
kubectl get pods -n ${NAMESPACE}

echo -e "\n${YELLOW}Services:${NC}"
kubectl get svc -n ${NAMESPACE}

# Get LoadBalancer IP
echo -e "\n${YELLOW}Getting LoadBalancer IP...${NC}"
EXTERNAL_IP=""
while [ -z $EXTERNAL_IP ]; do
    echo -e "${YELLOW}Waiting for LoadBalancer IP...${NC}"
    EXTERNAL_IP=$(kubectl get svc nginx-ingress-ingress-nginx-controller \
      -n ingress-nginx \
      -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    [ -z "$EXTERNAL_IP" ] && sleep 5
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}LoadBalancer External IP:${NC} ${GREEN}${EXTERNAL_IP}${NC}"
echo -e "\n${YELLOW}Access URLs:${NC}"
echo -e "  ${GREEN}Web:${NC}     http://${EXTERNAL_IP}/ (Host: ${DEFAULT_DOMAIN})"
echo -e "  ${GREEN}API:${NC}     http://${EXTERNAL_IP}/ (Host: ${API_DOMAIN})"
echo -e "  ${GREEN}Agents:${NC}  http://${EXTERNAL_IP}/ (Host: ${AGENTS_DOMAIN})"

echo -e "\n${YELLOW}To access via domain names, add to /etc/hosts:${NC}"
echo -e "${GREEN}${EXTERNAL_IP}  ${DEFAULT_DOMAIN}${NC}"
echo -e "${GREEN}${EXTERNAL_IP}  ${API_DOMAIN}${NC}"
echo -e "${GREEN}${EXTERNAL_IP}  ${AGENTS_DOMAIN}${NC}"

echo -e "\n${YELLOW}Quick Commands:${NC}"
echo -e "  ${GREEN}View logs:${NC}       kubectl logs -n ${NAMESPACE} -l app.kubernetes.io/component=api --tail=100 -f"
echo -e "  ${GREEN}Check pods:${NC}      kubectl get pods -n ${NAMESPACE}"
echo -e "  ${GREEN}Check ingress:${NC}   kubectl get ingress -n ${NAMESPACE}"
echo -e "  ${GREEN}Uninstall:${NC}       helm uninstall ${RELEASE_NAME} -n ${NAMESPACE}"

echo -e "\n${RED}IMPORTANT NEXT STEPS:${NC}"
echo -e "  1. Update Supabase credentials in the secret"
echo -e "  2. Update Google API key in the secret"
echo -e "  3. Configure DNS to point to ${EXTERNAL_IP}"
echo -e "  4. Enable TLS with cert-manager for production"

echo -e "\n${GREEN}Done!${NC}"
