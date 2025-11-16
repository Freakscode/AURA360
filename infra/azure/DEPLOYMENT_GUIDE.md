# AURA360 - Azure Deployment Guide

Guía completa para desplegar AURA360 en Azure Kubernetes Service (AKS).

## Estado Actual ✅

### Infraestructura de Azure (Terraform)
- ✅ **AKS Cluster**: `aura360-prod-aks` (Kubernetes 1.32, 2-5 nodos autoscaling)
- ✅ **Azure Container Registry**: `aura360prodacr.azurecr.io` (Premium)
- ✅ **Virtual Network**: Subnets configuradas para AKS y servicios
- ✅ **Key Vault**: `aura360prodkv` (para secretos)
- ✅ **Storage Account**: Configurado
- ✅ **Log Analytics**: Monitoring habilitado

### Imágenes Docker en ACR
Todas las imágenes construidas y disponibles:
- ✅ `aura360-api:latest` - Django REST API
- ✅ `aura360-agents:latest` - FastAPI Agents (Google ADK)
- ✅ `aura360-vectordb-api:latest` - Vector DB API
- ✅ `aura360-vectordb-worker:latest` - Celery Worker
- ✅ `aura360-web:latest` - Angular SSR Frontend

### Helm Charts
- ✅ Chart principal con templates completos
- ✅ Values para dev y prod
- ✅ Manifiestos de Kubernetes para todos los servicios
- ✅ Storage Classes de Azure Files configuradas
- ✅ Ingress NGINX configurado

## Prerequisitos

### 1. Instalar Herramientas

#### macOS
```bash
# Helm 3
brew install helm

# Verificar
helm version
```

#### Verificar Conexión a AKS
```bash
# Obtener credenciales
az aks get-credentials \
  --resource-group aura360-prod-rg \
  --name aura360-prod-aks \
  --overwrite-existing

# Verificar nodos
kubectl get nodes

# Deberías ver 2-3 nodos en estado Ready
```

### 2. Configurar Credenciales

#### Supabase
Necesitas obtener:
- URL del proyecto Supabase
- Service Role Key
- JWT Secret
- Anon Key

Estos valores se encuentran en: Supabase Dashboard → Project Settings → API

#### Google API
Necesitas:
- Google API Key con acceso a:
  - Generative AI API
  - Vertex AI API (opcional)

## Despliegue Rápido (Automated)

### Opción 1: Script Automático

```bash
# Desde la raíz del proyecto
cd infra/azure/helm

# Desplegar en ambiente de desarrollo
./deploy.sh dev

# O para producción
./deploy.sh prod
```

El script automáticamente:
1. ✅ Verifica prerrequisitos
2. ✅ Instala NGINX Ingress Controller
3. ✅ Crea secrets (con placeholders)
4. ✅ Despliega todos los servicios
5. ✅ Muestra la IP pública

### Opción 2: Despliegue Manual

#### Paso 1: Instalar NGINX Ingress

```bash
# Agregar repositorio
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Instalar
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz

# Esperar a que obtenga IP pública (toma 2-3 minutos)
kubectl get svc -n ingress-nginx -w
```

#### Paso 2: Configurar Secrets

```bash
# Crear namespace
kubectl create namespace aura360

# Supabase credentials
kubectl create secret generic supabase-credentials \
  --namespace aura360 \
  --from-literal=url='https://xxxxx.supabase.co' \
  --from-literal=service_role_key='eyJhbGci...' \
  --from-literal=jwt_secret='your-jwt-secret' \
  --from-literal=anon_key='eyJhbGci...'

# Google API credentials
kubectl create secret generic google-api-credentials \
  --namespace aura360 \
  --from-literal=api_key='AIzaSy...'
```

#### Paso 3: Desplegar AURA360

```bash
# Desde infra/azure/helm/
cd aura360

# Deploy con valores de desarrollo
helm install aura360 . \
  --namespace aura360 \
  --create-namespace \
  --values values.yaml \
  --values values-dev.yaml \
  --wait
```

#### Paso 4: Verificar Despliegue

```bash
# Ver todos los pods (deberían estar Running)
kubectl get pods -n aura360

# Ejemplo de salida esperada:
# NAME                            READY   STATUS    RESTARTS   AGE
# api-xxxxx                       1/1     Running   0          2m
# agents-xxxxx                    1/1     Running   0          2m
# vectordb-api-xxxxx              1/1     Running   0          2m
# vectordb-worker-xxxxx           1/1     Running   0          2m
# web-xxxxx                       1/1     Running   0          2m
# qdrant-xxxxx                    1/1     Running   0          2m
# redis-xxxxx                     1/1     Running   0          2m
# grobid-xxxxx                    1/1     Running   0          2m

# Ver servicios
kubectl get svc -n aura360

# Ver ingress
kubectl get ingress -n aura360
```

## Acceder a la Aplicación

### 1. Obtener IP Pública

```bash
EXTERNAL_IP=$(kubectl get svc nginx-ingress-ingress-nginx-controller \
  -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "IP Pública: $EXTERNAL_IP"
```

### 2. Configurar DNS Local (Para Testing)

Editar `/etc/hosts`:

```bash
sudo nano /etc/hosts

# Agregar:
<EXTERNAL_IP>  aura360-dev.eastus2.cloudapp.azure.com
<EXTERNAL_IP>  api-dev.eastus2.cloudapp.azure.com
<EXTERNAL_IP>  agents-dev.eastus2.cloudapp.azure.com
```

### 3. Acceder URLs

- **Web Frontend**: http://aura360-dev.eastus2.cloudapp.azure.com
- **API**: http://api-dev.eastus2.cloudapp.azure.com/api/v1/
- **Agents**: http://agents-dev.eastus2.cloudapp.azure.com/readyz

### 4. Pruebas de Health

```bash
# API Health
curl http://api-dev.eastus2.cloudapp.azure.com/api/v1/health

# Agents Health
curl http://agents-dev.eastus2.cloudapp.azure.com/readyz

# Qdrant
kubectl port-forward -n aura360 svc/qdrant 6333:6333
curl http://localhost:6333
```

## Configuración de Producción

### 1. DNS Real

En tu proveedor de DNS (Cloudflare, GoDaddy, etc.), crea registros A:

```
A  aura360.com              → <EXTERNAL_IP>
A  api.aura360.com          → <EXTERNAL_IP>
A  agents.aura360.com       → <EXTERNAL_IP>
```

### 2. Habilitar TLS con cert-manager

```bash
# Instalar cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Esperar a que esté listo
kubectl wait --for=condition=Available --timeout=300s \
  deployment/cert-manager -n cert-manager

# Crear ClusterIssuer
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

### 3. Actualizar Values de Producción

Editar `values-prod.yaml` con tus dominios reales y desplegar:

```bash
helm upgrade aura360 . \
  --namespace aura360 \
  --values values.yaml \
  --values values-prod.yaml
```

## Troubleshooting

### Pods no inician

```bash
# Ver detalles del pod
kubectl describe pod <pod-name> -n aura360

# Ver logs
kubectl logs -n aura360 <pod-name> --tail=100

# Logs en tiempo real
kubectl logs -n aura360 -l app.kubernetes.io/component=api -f
```

### Problemas de Storage

```bash
# Ver PVCs
kubectl get pvc -n aura360

# Si están Pending, verificar storage class
kubectl get sc

# Describir PVC
kubectl describe pvc qdrant-storage -n aura360
```

### Problemas de Ingress

```bash
# Ver ingress
kubectl describe ingress aura360-ingress -n aura360

# Logs de nginx-ingress
kubectl logs -n ingress-nginx \
  -l app.kubernetes.io/component=controller --tail=100 -f
```

### Secrets no encontrados

```bash
# Listar secrets
kubectl get secrets -n aura360

# Ver contenido (base64 encoded)
kubectl get secret supabase-credentials -n aura360 -o yaml

# Recrear secret
kubectl delete secret supabase-credentials -n aura360
kubectl create secret generic supabase-credentials \
  --namespace aura360 \
  --from-literal=url='...' \
  --from-literal=service_role_key='...' \
  --from-literal=jwt_secret='...' \
  --from-literal=anon_key='...'
```

## Monitoreo

### Recursos

```bash
# Top nodos
kubectl top nodes

# Top pods
kubectl top pods -n aura360
```

### Logs Centralizados

```bash
# Ver logs de todos los pods API
kubectl logs -n aura360 -l app.kubernetes.io/component=api --tail=100

# Seguir logs en tiempo real
kubectl logs -n aura360 -l app.kubernetes.io/component=agents -f
```

## Actualizar Aplicación

### 1. Construir Nuevas Imágenes

```bash
# Ejemplo para API
cd services/api
docker build -t aura360prodacr.azurecr.io/aura360-api:v1.1.0 .
docker push aura360prodacr.azurecr.io/aura360-api:v1.1.0
```

### 2. Actualizar Helm Chart

```bash
# Actualizar tag en values.yaml o usar --set
helm upgrade aura360 . \
  --namespace aura360 \
  --values values.yaml \
  --values values-dev.yaml \
  --set api.image.tag=v1.1.0
```

### 3. Rollback si es necesario

```bash
# Ver historia
helm history aura360 -n aura360

# Rollback a revisión anterior
helm rollback aura360 -n aura360
```

## Desinstalar

```bash
# Eliminar release
helm uninstall aura360 -n aura360

# Eliminar namespace (esto borra PVCs también)
kubectl delete namespace aura360

# Eliminar ingress controller (opcional)
helm uninstall nginx-ingress -n ingress-nginx
kubectl delete namespace ingress-nginx
```

## Próximos Pasos

1. **Configurar CI/CD** con GitHub Actions o Azure DevOps
2. **Implementar Monitoring** con Prometheus + Grafana
3. **Configurar Backups** de PVCs
4. **Configurar Alerting** para incidentes
5. **Implementar Logging** centralizado (ELK o Azure Monitor)
6. **Security Scanning** de imágenes
7. **Network Policies** para seguridad

## Soporte

- Ver [README del Helm Chart](helm/aura360/README.md)
- Ver [CLAUDE.md](../../docs/runbooks/agents/CLAUDE.md) para arquitectura
- Abrir issue en el repositorio del proyecto
