#!/usr/bin/env python3
"""
Script para insertar datos de prueba en Qdrant Cloud.

Uso:
    python insert_test_data.py
"""

import os
import sys
import uuid
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from infra.settings import get_settings


# Documentos de prueba sobre nutrición y wellness
TEST_DOCUMENTS = [
    {
        "id": str(uuid.uuid4()),
        "text": "El ejercicio cardiovascular regular es fundamental para la salud del corazón. Se recomienda al menos 150 minutos de actividad moderada por semana, como caminar rápido, nadar o andar en bicicleta. El cardio ayuda a mejorar la circulación, reduce la presión arterial y aumenta la capacidad pulmonar.",
        "metadata": {
            "topic": "ejercicio",
            "category": "cardiovascular",
            "source": "guia-ejercicio.pdf",
            "lang": "es",
            "confidence_score": 0.95
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Una dieta equilibrada debe incluir proteínas magras, carbohidratos complejos y grasas saludables. Las proteínas ayudan a construir y reparar tejidos, los carbohidratos proporcionan energía sostenida, y las grasas omega-3 son esenciales para la salud cerebral y cardiovascular.",
        "metadata": {
            "topic": "nutrición",
            "category": "alimentación_equilibrada",
            "source": "manual-nutricion.pdf",
            "lang": "es",
            "confidence_score": 0.92
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "El sueño reparador es crucial para la salud mental y física. Durante el sueño profundo, el cuerpo repara tejidos, consolida la memoria y regula hormonas. Se recomienda dormir entre 7-9 horas por noche en un ambiente oscuro y fresco.",
        "metadata": {
            "topic": "sueño",
            "category": "descanso",
            "source": "salud-integral.pdf",
            "lang": "es",
            "confidence_score": 0.88
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "La hidratación adecuada es esencial para todas las funciones corporales. Se recomienda beber al menos 2 litros de agua al día, más si haces ejercicio intenso. El agua ayuda a transportar nutrientes, regular la temperatura corporal y eliminar toxinas.",
        "metadata": {
            "topic": "hidratación",
            "category": "nutrición",
            "source": "guia-hidratacion.pdf",
            "lang": "es",
            "confidence_score": 0.90
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "El estrés crónico puede afectar negativamente la salud física y mental. Técnicas como la meditación, respiración profunda y yoga pueden ayudar a reducir los niveles de cortisol y promover la relajación. Dedica al menos 10-15 minutos diarios a prácticas de mindfulness.",
        "metadata": {
            "topic": "salud_mental",
            "category": "manejo_estrés",
            "source": "bienestar-mental.pdf",
            "lang": "es",
            "confidence_score": 0.91
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "El entrenamiento de fuerza es importante para mantener la masa muscular, especialmente después de los 30 años. Se recomienda trabajar todos los grupos musculares principales 2-3 veces por semana. Esto ayuda a mejorar el metabolismo, la densidad ósea y la postura.",
        "metadata": {
            "topic": "ejercicio",
            "category": "fuerza",
            "source": "guia-ejercicio.pdf",
            "lang": "es",
            "confidence_score": 0.93
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "Los antioxidantes presentes en frutas y verduras coloridas ayudan a combatir el daño celular causado por los radicales libres. Consume una variedad de colores: naranjas (betacaroteno), rojos (licopeno), verdes (clorofila) y morados (antocianinas).",
        "metadata": {
            "topic": "nutrición",
            "category": "antioxidantes",
            "source": "manual-nutricion.pdf",
            "lang": "es",
            "confidence_score": 0.89
        }
    },
    {
        "id": str(uuid.uuid4()),
        "text": "La vitamina D es esencial para la salud ósea y el sistema inmunológico. Aunque el sol es una fuente natural, muchas personas necesitan suplementación, especialmente en invierno. Consulta con tu médico sobre tus niveles de vitamina D.",
        "metadata": {
            "topic": "vitaminas",
            "category": "suplementación",
            "source": "guia-vitaminas.pdf",
            "lang": "es",
            "confidence_score": 0.87
        }
    }
]


def generate_embedding(text: str, dimension: int = 384) -> list[float]:
    """
    Genera un embedding simulado basado en el texto.
    En producción, esto debería usar un modelo real (FastEmbed, Gemini, etc).
    """
    import random
    import hashlib
    import math

    # Usar hash del texto como seed para consistencia
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    random.seed(seed)

    # Generar vector aleatorio
    vector = [random.gauss(0, 0.3) for _ in range(dimension)]

    # Normalizar para distancia coseno
    magnitude = math.sqrt(sum(x*x for x in vector))
    vector = [x/magnitude for x in vector]

    return vector


def insert_test_data(collection_name: str = "holistic_memory"):
    """Inserta datos de prueba en Qdrant Cloud."""
    print("=" * 70)
    print(f"  📥 INSERTAR DATOS DE PRUEBA EN: {collection_name}")
    print("=" * 70)

    # Obtener configuración
    settings = get_settings()

    print(f"\n📍 URL: {settings.vector_service_url}")
    print(f"📦 Colección: {collection_name}")

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
        return False

    # Obtener dimensión de la colección
    try:
        info = client.get_collection(collection_name)
        vector_dimension = info.config.params.vectors.size
        print(f"📏 Dimensión de vectores: {vector_dimension}")
    except Exception as e:
        print(f"❌ Error obteniendo info de colección: {e}")
        return False

    # Preparar puntos
    print(f"\n🔨 Preparando {len(TEST_DOCUMENTS)} documentos...")
    points = []

    for i, doc in enumerate(TEST_DOCUMENTS, 1):
        # Generar embedding
        embedding = generate_embedding(doc["text"], dimension=vector_dimension)

        # Crear payload
        payload = {
            "text": doc["text"],
            **doc["metadata"]
        }

        # Crear punto
        point = PointStruct(
            id=doc["id"],
            vector=embedding,
            payload=payload
        )

        points.append(point)

        # Mostrar progreso
        text_preview = doc["text"][:80] + "..." if len(doc["text"]) > 80 else doc["text"]
        print(f"   {i}. {doc['metadata']['topic']}: {text_preview}")

    # Insertar en Qdrant
    print(f"\n📤 Insertando puntos en Qdrant Cloud...")
    try:
        client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True
        )
        print(f"✅ {len(points)} puntos insertados exitosamente!\n")
    except Exception as e:
        print(f"❌ Error insertando puntos: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Verificar inserción
    print(f"🔍 Verificando inserción...")
    try:
        info = client.get_collection(collection_name)
        print(f"✅ Total de vectores en la colección: {info.points_count:,}\n")
    except Exception as e:
        print(f"⚠️  Error verificando: {e}\n")

    return True


def main():
    """Función principal."""
    print("\n" + "📥" * 35)
    print("  INSERTAR DATOS DE PRUEBA EN QDRANT CLOUD")
    print("📥" * 35 + "\n")

    # Insertar en holistic_memory (384 dimensiones)
    success_memory = insert_test_data("holistic_memory")

    # También insertar en holistic_agents si existe (768 dimensiones)
    print("\n" + "-" * 70 + "\n")
    success_agents = insert_test_data("holistic_agents")

    # Resumen
    print("=" * 70)
    print("  ✅ INSERCIÓN COMPLETADA")
    print("=" * 70)

    if success_memory:
        print(f"\n✅ holistic_memory: {len(TEST_DOCUMENTS)} documentos insertados")
    if success_agents:
        print(f"✅ holistic_agents: {len(TEST_DOCUMENTS)} documentos insertados")

    print("\n💡 Ahora puedes ejecutar test_qdrant_connection.py para probar búsquedas\n")


if __name__ == "__main__":
    main()
