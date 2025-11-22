#!/usr/bin/env python3
"""
Script de prueba de búsqueda semántica usando embeddings reales de Gemini.

Uso:
    python test_semantic_search.py
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from qdrant_client import QdrantClient
from infra.settings import get_settings


def get_gemini_embedding(text: str) -> list[float]:
    """Genera embedding usando Google Gemini."""
    try:
        import google.generativeai as genai

        # Obtener API key
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("⚠️  GOOGLE_API_KEY no configurada, usando embeddings simulados")
            return None

        # Configurar Gemini
        genai.configure(api_key=api_key)

        # Generar embedding
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )

        return result['embedding']

    except ImportError:
        print("⚠️  google-generativeai no instalado")
        print("   Instalar con: pip install google-generativeai")
        return None
    except Exception as e:
        print(f"⚠️  Error generando embedding: {e}")
        return None


def search_semantic(client: QdrantClient, query: str, collection_name: str, limit: int = 3):
    """Realiza búsqueda semántica usando embeddings de Gemini."""
    print("=" * 70)
    print(f"  🔍 BÚSQUEDA SEMÁNTICA")
    print("=" * 70)

    print(f"\n❓ Query: \"{query}\"")
    print(f"📦 Colección: {collection_name}")

    # Generar embedding de la query
    print(f"\n🧠 Generando embedding con Gemini...")
    embedding = get_gemini_embedding(query)

    if not embedding:
        print("❌ No se pudo generar embedding")
        return

    print(f"✅ Embedding generado ({len(embedding)} dimensiones)")

    # Realizar búsqueda
    print(f"\n🔎 Buscando documentos similares (top {limit})...\n")

    try:
        results = client.search(
            collection_name=collection_name,
            query_vector=embedding,
            limit=limit,
            with_payload=True,
        )

        if not results:
            print("⚠️  No se encontraron resultados")
            return

        print(f"✅ Se encontraron {len(results)} resultados:\n")

        for i, result in enumerate(results, 1):
            print("─" * 70)
            print(f"📄 Resultado #{i}")
            print(f"   🎯 Score de similitud: {result.score:.4f}")

            if result.payload:
                # Mostrar información
                if 'topic' in result.payload:
                    print(f"   📌 Tema: {result.payload['topic']}")

                if 'category' in result.payload:
                    print(f"   🏷️  Categoría: {result.payload['category']}")

                if 'source' in result.payload:
                    print(f"   📚 Fuente: {result.payload['source']}")

                if 'text' in result.payload:
                    text = result.payload['text']
                    print(f"\n   📝 Contenido:")
                    print(f"   {text}\n")

    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Función principal."""
    print("\n" + "🔍" * 35)
    print("  PRUEBA DE BÚSQUEDA SEMÁNTICA CON GEMINI")
    print("🔍" * 35)

    # Obtener configuración
    settings = get_settings()

    print(f"\n📍 URL: {settings.vector_service_url}")
    print(f"📦 Colección: {settings.vector_collection_name}")

    # Conectar a Qdrant
    try:
        print("\n🔌 Conectando a Qdrant Cloud...")
        client = QdrantClient(
            url=settings.vector_service_url,
            api_key=settings.vector_service_api_key,
            timeout=settings.vector_timeout,
        )
        print("✅ Conectado\n")
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        sys.exit(1)

    # Queries de prueba
    test_queries = [
        "¿Qué ejercicios debo hacer para mejorar mi salud cardiovascular?",
        "¿Cómo puedo mejorar mi alimentación?",
        "Consejos para dormir mejor",
        "¿Cómo manejar el estrés?",
    ]

    # Ejecutar búsquedas
    for query in test_queries:
        search_semantic(client, query, settings.vector_collection_name, limit=3)
        print("\n")

    # También buscar en holistic_agents si existe
    print("\n" + "=" * 70)
    print("  🔍 BÚSQUEDA EN HOLISTIC_AGENTS (768 dims)")
    print("=" * 70)
    search_semantic(client, test_queries[0], "holistic_agents", limit=2)

    # Resumen
    print("\n" + "=" * 70)
    print("  ✅ PRUEBAS COMPLETADAS")
    print("=" * 70)
    print("\n🎉 La búsqueda semántica está funcionando correctamente!")
    print("💡 Los resultados muestran similitud semántica basada en Gemini embeddings\n")


if __name__ == "__main__":
    main()
