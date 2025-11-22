#!/usr/bin/env python3
"""
Script para inicializar las colecciones necesarias en Qdrant Cloud.

Uso:
    python scripts/init_qdrant_collections.py

Requiere variables de entorno:
    QDRANT_URL - URL del cluster de Qdrant Cloud
    QDRANT_API_KEY - API key del cluster

Ejemplo:
    export QDRANT_URL="https://abc-xyz.us-central1-0.gcp.cloud.qdrant.io:6333"
    export QDRANT_API_KEY="your-api-key"
    python scripts/init_qdrant_collections.py
"""

import os
import sys
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


# Definición de colecciones necesarias para AURA360
COLLECTIONS = {
    "holistic_memory": {
        "description": "Almacena embeddings de contexto de usuario y documentos holísticos",
        "vector_size": 384,
        "distance": Distance.COSINE,
    },
    "user_context": {
        "description": "Almacena contexto agregado de usuarios (eventos, actividades, preferencias)",
        "vector_size": 384,
        "distance": Distance.COSINE,
    },
    "holistic_agents": {
        "description": "Almacena embeddings para el servicio de agents (RAG)",
        "vector_size": 768,  # Gemini text-embedding-004
        "distance": Distance.COSINE,
    },
}


def get_qdrant_client() -> Optional[QdrantClient]:
    """Crea cliente de Qdrant desde variables de entorno."""
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url:
        print("❌ Error: QDRANT_URL no está configurada")
        print("   export QDRANT_URL='https://your-cluster.gcp.cloud.qdrant.io:6333'")
        return None

    # API key es opcional para desarrollo local, pero requerido para Cloud
    if "cloud.qdrant.io" in qdrant_url and not qdrant_api_key:
        print("❌ Error: QDRANT_API_KEY es requerida para Qdrant Cloud")
        print("   export QDRANT_API_KEY='your-api-key'")
        return None

    print(f"🔗 Conectando a Qdrant: {qdrant_url}")

    try:
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10,
        )
        # Test de conexión
        client.get_collections()
        print("✅ Conexión exitosa a Qdrant\n")
        return client
    except Exception as e:
        print(f"❌ Error conectando a Qdrant: {e}")
        return None


def create_collection(
    client: QdrantClient,
    name: str,
    vector_size: int,
    distance: Distance,
    description: str,
) -> bool:
    """Crea una colección en Qdrant si no existe."""
    try:
        # Verificar si la colección ya existe
        collections = client.get_collections().collections
        existing = [c.name for c in collections]

        if name in existing:
            print(f"⏭️  Colección '{name}' ya existe, omitiendo...")
            # Mostrar info de la colección existente
            info = client.get_collection(name)
            print(f"   Vectores: {info.points_count}")
            print(f"   Dimensión: {info.config.params.vectors.size}")
            print(f"   Distancia: {info.config.params.vectors.distance}\n")
            return True

        # Crear colección
        print(f"📦 Creando colección '{name}'...")
        print(f"   {description}")
        print(f"   Dimensión: {vector_size}, Distancia: {distance.value}")

        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance,
            ),
        )

        print(f"✅ Colección '{name}' creada exitosamente\n")
        return True

    except Exception as e:
        print(f"❌ Error creando colección '{name}': {e}\n")
        return False


def main():
    """Punto de entrada principal."""
    print("=" * 70)
    print("  Inicialización de Colecciones en Qdrant Cloud - AURA360")
    print("=" * 70)
    print()

    # Obtener cliente
    client = get_qdrant_client()
    if not client:
        sys.exit(1)

    # Crear colecciones
    success_count = 0
    total_count = len(COLLECTIONS)

    for name, config in COLLECTIONS.items():
        if create_collection(
            client=client,
            name=name,
            vector_size=config["vector_size"],
            distance=config["distance"],
            description=config["description"],
        ):
            success_count += 1

    # Resumen
    print("=" * 70)
    print(f"✅ Inicialización completada: {success_count}/{total_count} colecciones")
    print("=" * 70)
    print()

    # Listar todas las colecciones
    print("📋 Colecciones disponibles en Qdrant:")
    collections = client.get_collections().collections
    for col in collections:
        info = client.get_collection(col.name)
        print(f"   • {col.name}")
        print(f"     Vectores: {info.points_count}")
        print(f"     Dimensión: {info.config.params.vectors.size}")
        print(f"     Distancia: {info.config.params.vectors.distance}")
        print()

    if success_count < total_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
