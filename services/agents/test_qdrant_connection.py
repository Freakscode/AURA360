#!/usr/bin/env python3
"""
Script de prueba para verificar conexión a Qdrant Cloud desde el servicio de agentes.

Uso:
    python test_qdrant_connection.py
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from infra.settings import get_settings


def print_header(title: str):
    """Imprime un encabezado decorado."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_connection():
    """Prueba la conexión a Qdrant Cloud."""
    print_header("🔗 PRUEBA DE CONEXIÓN A QDRANT CLOUD")

    # Obtener configuración
    settings = get_settings()

    print(f"\n📍 URL: {settings.vector_service_url}")
    print(f"🔑 API Key: {'***' + settings.vector_service_api_key[-8:] if settings.vector_service_api_key else 'No configurada'}")
    print(f"📦 Colección configurada: {settings.vector_collection_name}")
    print(f"⏱️  Timeout: {settings.vector_timeout}s")
    print(f"🔒 Verify SSL: {settings.vector_verify_ssl}")

    # Crear cliente
    try:
        print("\n🔌 Conectando a Qdrant Cloud...")
        client = QdrantClient(
            url=settings.vector_service_url,
            api_key=settings.vector_service_api_key,
            timeout=settings.vector_timeout,
        )
        print("✅ Conexión establecida exitosamente\n")
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return False

    return client


def list_collections(client: QdrantClient):
    """Lista todas las colecciones disponibles."""
    print_header("📚 COLECCIONES DISPONIBLES")

    try:
        collections_response = client.get_collections()
        collections = collections_response.collections

        if not collections:
            print("\n⚠️  No hay colecciones disponibles")
            return []

        print(f"\n📊 Total de colecciones: {len(collections)}\n")

        collection_names = []
        for col in collections:
            collection_names.append(col.name)

            # Obtener información detallada
            try:
                info = client.get_collection(col.name)

                print(f"📦 Colección: {col.name}")
                print(f"   ├─ Vectores: {info.points_count:,}")
                print(f"   ├─ Dimensión: {info.config.params.vectors.size}")
                print(f"   ├─ Distancia: {info.config.params.vectors.distance}")
                print(f"   └─ Status: {info.status}")
                print()
            except Exception as e:
                print(f"   └─ ⚠️  Error obteniendo info: {e}\n")

        return collection_names

    except Exception as e:
        print(f"\n❌ Error listando colecciones: {e}")
        return []


def inspect_collection(client: QdrantClient, collection_name: str):
    """Inspecciona una colección específica."""
    print_header(f"🔍 INSPECCIONANDO COLECCIÓN: {collection_name}")

    try:
        # Obtener información
        info = client.get_collection(collection_name)

        print(f"\n📊 Estadísticas:")
        print(f"   ├─ Total de puntos: {info.points_count:,}")
        print(f"   ├─ Dimensión de vectores: {info.config.params.vectors.size}")
        print(f"   ├─ Métrica de distancia: {info.config.params.vectors.distance}")
        print(f"   └─ Status: {info.status}")

        # Intentar obtener algunos puntos de muestra
        if info.points_count > 0:
            print(f"\n📄 Obteniendo muestra de puntos...")
            try:
                # Scroll para obtener algunos puntos
                records, next_offset = client.scroll(
                    collection_name=collection_name,
                    limit=3,
                    with_payload=True,
                    with_vectors=False,
                )

                if records:
                    print(f"   ✅ Se encontraron {len(records)} puntos de muestra:\n")
                    for i, record in enumerate(records, 1):
                        print(f"   Punto #{i}:")
                        print(f"      ID: {record.id}")
                        if record.payload:
                            # Mostrar algunos campos del payload
                            payload_preview = {k: v for k, v in list(record.payload.items())[:5]}
                            print(f"      Payload (preview): {payload_preview}")
                        print()
                else:
                    print(f"   ⚠️  No se pudieron obtener puntos")
            except Exception as e:
                print(f"   ⚠️  Error obteniendo puntos: {e}")
        else:
            print(f"\n⚠️  La colección está vacía")

        return True

    except Exception as e:
        print(f"\n❌ Error inspeccionando colección: {e}")
        return False


def test_search(client: QdrantClient, collection_name: str):
    """Prueba una búsqueda de vectores."""
    print_header(f"🔎 PRUEBA DE BÚSQUEDA EN: {collection_name}")

    try:
        # Obtener información de la colección
        info = client.get_collection(collection_name)
        vector_size = info.config.params.vectors.size

        if info.points_count == 0:
            print(f"\n⚠️  La colección está vacía, no se puede hacer búsqueda")
            return False

        print(f"\n🎯 Creando vector de prueba ({vector_size} dimensiones)...")

        # Crear un vector de prueba (valores aleatorios normalizados)
        import random
        import math

        # Generar vector aleatorio
        test_vector = [random.gauss(0, 0.3) for _ in range(vector_size)]

        # Normalizar el vector
        magnitude = math.sqrt(sum(x*x for x in test_vector))
        test_vector = [x/magnitude for x in test_vector]

        print(f"✅ Vector de prueba creado")
        print(f"   Primeros 5 valores: {[f'{v:.4f}' for v in test_vector[:5]]}")

        # Realizar búsqueda
        print(f"\n🔍 Realizando búsqueda (top 3)...")
        results = client.search(
            collection_name=collection_name,
            query_vector=test_vector,
            limit=3,
            with_payload=True,
        )

        if results:
            print(f"\n✅ Búsqueda exitosa! Se encontraron {len(results)} resultados:\n")

            for i, result in enumerate(results, 1):
                print(f"   Resultado #{i}:")
                print(f"      ├─ Score: {result.score:.4f}")
                print(f"      ├─ ID: {result.id}")

                if result.payload:
                    # Mostrar campos relevantes
                    payload_preview = {}
                    for key in ['text', 'title', 'source', 'topic', 'doc_id']:
                        if key in result.payload:
                            value = result.payload[key]
                            if key == 'text' and isinstance(value, str) and len(value) > 100:
                                value = value[:100] + "..."
                            payload_preview[key] = value

                    if payload_preview:
                        print(f"      └─ Payload:")
                        for k, v in payload_preview.items():
                            print(f"         • {k}: {v}")
                print()

            return True
        else:
            print(f"\n⚠️  No se encontraron resultados")
            return False

    except Exception as e:
        print(f"\n❌ Error en búsqueda: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal."""
    print("\n" + "🚀" * 35)
    print("  TEST DE CONEXIÓN: Agents Service → Qdrant Cloud")
    print("🚀" * 35)

    # Test de conexión
    client = test_connection()
    if not client:
        print("\n❌ Prueba fallida: No se pudo conectar a Qdrant Cloud")
        sys.exit(1)

    # Listar colecciones
    collections = list_collections(client)

    if not collections:
        print("\n⚠️  No hay colecciones para probar")
        sys.exit(0)

    # Inspeccionar la colección configurada
    settings = get_settings()
    target_collection = settings.vector_collection_name

    if target_collection in collections:
        inspect_collection(client, target_collection)
        test_search(client, target_collection)
    else:
        print(f"\n⚠️  La colección configurada '{target_collection}' no existe")
        print(f"   Colecciones disponibles: {', '.join(collections)}")

        # Probar con la primera colección disponible
        if collections:
            first_collection = collections[0]
            print(f"\n📦 Probando con la primera colección disponible: {first_collection}")
            inspect_collection(client, first_collection)
            test_search(client, first_collection)

    # Resumen final
    print_header("✅ PRUEBA COMPLETADA")
    print(f"\n🎉 La conexión a Qdrant Cloud está funcionando correctamente!")
    print(f"📊 Se encontraron {len(collections)} colecciones")
    print(f"🔗 URL: {settings.vector_service_url}\n")


if __name__ == "__main__":
    main()
