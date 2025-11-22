# Cómo Obtener la URL de Qdrant Cloud

## Opción 1: Desde la Consola Web

1. **Ir a Qdrant Cloud Console**: https://cloud.qdrant.io
2. **Login** con tu cuenta
3. **Seleccionar tu cluster** (debería aparecer en el dashboard)
4. **En la página del cluster**, busca:
   - **"Cluster URL"** o **"API Endpoint"**
   - Debería tener el formato:
     ```
     https://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX.us-central1-0.gcp.cloud.qdrant.io:6333
     ```
   - O similar con otra región

5. **Copiar la URL completa** (incluyendo el puerto `:6333`)

## Opción 2: Desde la CLI (si la tienes instalada)

```bash
# Listar clusters
qdrant-cloud cluster list

# Ver detalles del cluster
qdrant-cloud cluster get <cluster-name>
```

## Formato de la URL

La URL de Qdrant Cloud siempre tiene este formato:

```
https://<cluster-id>.<region>.gcp.cloud.qdrant.io:6333
```

Donde:
- `<cluster-id>`: ID único de tu cluster (UUID)
- `<region>`: Región de GCP donde creaste el cluster
  - `us-central1-0` (Iowa)
  - `us-east1-0` (South Carolina)
  - `europe-west1-0` (Belgium)
  - etc.

## Ejemplo Completo

```bash
# URL típica de Qdrant Cloud en GCP
QDRANT_URL=https://abc12345-6789-abcd-ef01-23456789abcd.us-central1-0.gcp.cloud.qdrant.io:6333

# API Key (la que ya tienes)
QDRANT_API_KEY=tu-api-key-aqui
```

## ¿No encuentras el cluster?

Si no ves ningún cluster en la consola:
1. Verifica que estés en la cuenta correcta
2. Si vienes desde GCP Marketplace, deberías haber sido redirigido a crear un cluster
3. Si aún no has creado el cluster, ve a "Create Cluster" en la consola

## Test de Conexión

Una vez que tengas la URL y API Key:

```bash
# Test con curl
curl -H "api-key: TU_API_KEY" \
  https://tu-cluster.us-central1-0.gcp.cloud.qdrant.io:6333/collections

# Debería retornar JSON con lista de colecciones (vacía si es nuevo)
```
