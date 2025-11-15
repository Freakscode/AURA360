#!/usr/bin/env python3
"""Script para crear la colección user_context en Qdrant.

Esta colección almacena embeddings del contexto personalizado de cada usuario
(snapshots de mind, body, soul, holistic) que se usan con mayor peso que el
corpus general en las búsquedas.

Usage:
    python scripts/create_user_context_collection.py [--recreate]
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from vectosvc.config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_user_context_collection(
    client: QdrantClient, collection_name: str, vector_size: int, recreate: bool = False
):
    """Crea la colección user_context en Qdrant.

    Args:
        client: Cliente de Qdrant
        collection_name: Nombre de la colección (default: 'user_context')
        vector_size: Dimensión de los vectores de embedding
        recreate: Si True, elimina y recrea la colección si ya existe
    """
    # Verificar si la colección ya existe
    collections = client.get_collections().collections
    exists = any(col.name == collection_name for col in collections)

    if exists:
        if recreate:
            logger.warning(f"Colección '{collection_name}' existe. Eliminando...")
            client.delete_collection(collection_name)
            logger.info(f"Colección '{collection_name}' eliminada")
        else:
            logger.info(f"Colección '{collection_name}' ya existe. Use --recreate para forzar recreación.")
            return

    # Crear colección
    logger.info(f"Creando colección '{collection_name}' con dimensión {vector_size}...")

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,  # Usar cosine similarity
        ),
    )

    logger.info(f"✅ Colección '{collection_name}' creada exitosamente")

    # Crear índices para filtros comunes
    logger.info("Creando índices de payload...")

    # Índice por user_id (crítico para filtrado weighted)
    client.create_payload_index(
        collection_name=collection_name,
        field_name="user_id",
        field_schema="keyword",
    )

    # Índice por snapshot_type
    client.create_payload_index(
        collection_name=collection_name,
        field_name="snapshot_type",
        field_schema="keyword",
    )

    # Índice por category
    client.create_payload_index(
        collection_name=collection_name,
        field_name="category",
        field_schema="keyword",
    )

    # Índice por source_type
    client.create_payload_index(
        collection_name=collection_name,
        field_name="source_type",
        field_schema="keyword",
    )

    # Índice por topics (array)
    client.create_payload_index(
        collection_name=collection_name,
        field_name="topics",
        field_schema="keyword",
    )

    logger.info("✅ Índices creados exitosamente")

    # Insertar un punto de prueba para validar
    logger.info("Insertando punto de prueba...")

    import uuid

    test_point = PointStruct(
        id=str(uuid.uuid4()),  # UUID como string
        vector=[0.1] * vector_size,
        payload={
            "doc_id": "test_user_context_point",
            "text": "Test user context snapshot for validation",
            "user_id": "00000000-0000-0000-0000-000000000000",
            "snapshot_type": "holistic",
            "timeframe": "7d",
            "category": "mente",
            "source_type": "user_context",
            "topics": ["mental_health", "stress_response"],
            "created_at": "2025-01-01T00:00:00Z",
            "embedding_model": settings.embedding_model,
            "version": "1.0.0",
        },
    )

    client.upsert(
        collection_name=collection_name,
        points=[test_point],
    )

    logger.info("✅ Punto de prueba insertado")

    # Verificar
    info = client.get_collection(collection_name)
    logger.info(f"\nInformación de la colección:")
    logger.info(f"  Nombre: {collection_name}")
    logger.info(f"  Puntos: {info.points_count}")
    try:
        logger.info(f"  Dimensión: {info.config.params.vectors.size}")
        logger.info(f"  Distancia: {info.config.params.vectors.distance}")
    except AttributeError:
        # Versión diferente de la API
        logger.info(f"  Configuración: {info.config}")

    logger.info(f"\n✅ Colección '{collection_name}' lista para uso")


def main():
    parser = argparse.ArgumentParser(
        description="Crear colección user_context en Qdrant"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Eliminar y recrear la colección si ya existe",
    )
    parser.add_argument(
        "--collection-name",
        default="user_context",
        help="Nombre de la colección (default: user_context)",
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        default=None,
        help=f"Dimensión de los vectores (default: {settings.embedding_dim})",
    )

    args = parser.parse_args()

    # Conectar a Qdrant
    logger.info(f"Conectando a Qdrant en {settings.qdrant_url}...")

    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        prefer_grpc=settings.prefer_grpc,
    )

    logger.info("✅ Conectado a Qdrant")

    # Obtener dimensión de vectores
    vector_size = args.vector_size or settings.embedding_dim

    # Crear colección
    create_user_context_collection(
        client=client,
        collection_name=args.collection_name,
        vector_size=vector_size,
        recreate=args.recreate,
    )


if __name__ == "__main__":
    main()
