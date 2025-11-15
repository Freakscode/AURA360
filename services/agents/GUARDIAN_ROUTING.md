# Guardian Routing Especializado - Documentación de Implementación

## Resumen

Se ha implementado un sistema de routing inteligente que permite a cada Guardian (Mental, Physical, Spiritual) buscar en espacios vectoriales especializados de acuerdo a su dominio de conocimiento, con mapeo LLM de contexto a topics biomédicos y boosting de metadata.

## Arquitectura

### Componentes Implementados

#### 1. **TopicClassifier** (`services/topic_classifier.py`)
Servicio de clasificación LLM que mapea el contexto del usuario a topics biomédicos.

**Características:**
- Usa Gemini 2.0 Flash para clasificación semántica
- Mapea a 34 topics biomédicos definidos en `vectordb/config/topics.yaml`
- Cache en memoria para evitar costos repetidos
- Fallback con keyword matching si el LLM falla
- Retorna entre 1-5 topics relevantes por contexto

**Uso:**
```python
from services.topic_classifier import get_topic_classifier

classifier = get_topic_classifier()
topics = classifier.classify("Tengo problemas para dormir")
# Output: ["sleep_health", "insomnia", "circadian_rhythm"]
```

#### 2. **VectorSearchFilters** (`services/vector_queries.py`)
Dataclass que encapsula filtros para búsqueda vectorial especializada.

**Campos:**
- `category`: Filtro por categoría ("mente", "cuerpo", "alma")
- `topics`: Lista de topics biomédicos para filtrar
- `min_year`: Año mínimo de publicación
- `locale`: Filtro por idioma/región (e.g., "es-CO")
- `boost_abstracts`: Activar boosting de abstracts/conclusions (+0.2)
- `boost_recent`: Activar boosting de papers recientes (+0.15 para 2020+)

#### 3. **VectorQueryRunner** (extendido)
Ahora soporta filtros avanzados y boosting de scores.

**Nuevas funcionalidades:**
- Acepta parámetro `filters: VectorSearchFilters`
- Construye filtros Qdrant dinámicamente
- Aplica boosting post-búsqueda basado en metadata
- Retorna scores ajustados con información de boost

**Filtros Qdrant generados:**
- Filtro por `category` (match exact)
- Filtro por `topics` (match any)
- Filtro por `year` (range ≥ min_year)
- Filtro por `locale` (match exact)

**Boosting aplicado:**
- Abstracts/conclusions: +0.2
- Papers 2020+: +0.15
- Papers 2015-2019: +0.1

#### 4. **GuardianKnowledgeRetriever** (`services/guardian_retrieval.py`)
Servicio principal de routing especializado por Guardian.

**Métodos:**
- `retrieve_for_mental()`: Búsqueda especializada para Mental Guardian
- `retrieve_for_physical()`: Búsqueda especializada para Physical Guardian
- `retrieve_for_spiritual()`: Búsqueda especializada para Spiritual Guardian

**Flujo de trabajo:**
1. Clasifica topics del contexto (si no se proporcionan)
2. Filtra topics relevantes al dominio del Guardian
3. Construye filtros Qdrant con categoría + topics
4. Ejecuta búsqueda vectorial con boosting
5. Maneja fallback si no hay resultados

**Fallback strategy:**
- Si no hay topics relevantes en el dominio → usa todos los topics del Guardian
- Si la búsqueda falla → reintenta sin filtros de topics
- Si falla completamente → retorna lista vacía

#### 5. **GUARDIAN_KNOWLEDGE_DOMAINS** (`infra/settings.py`)
Configuración de dominios de conocimiento por Guardian.

**Dominios definidos:**

**Mental Guardian:**
- mental_health, cognitive_function, neurodegeneration
- stress_response, neuroendocrine, metabolic_brain
- chronic_pain

**Physical Guardian:**
- nutrition, exercise_physiology, sleep_health
- circadian_rhythm, sleep_deprivation, insomnia
- hypersomnia, obstructive_sleep_apnea, sleep_medicine
- gut_microbiome, metabolism_disorders, obesity
- type2_diabetes, insulin_signaling, cardiovascular_health
- chrononutrition, liver_health, immunometabolism
- endocrine_disorders, inflammation, oxidative_stress

**Spiritual Guardian:**
- aging_longevity, reproductive_health, pcos
- adolescent_health
- mental_health, stress_response (overlap intencional con Mental)

#### 6. **HolisticAdviceService** (actualizado)
Orquestador principal que integra el routing especializado.

**Cambios:**
- Agrega `_guardian_retriever` y `_topic_classifier` en constructor
- Nuevo método `_run_specialized_vector_query()`
- `generate_advice()` ahora:
  1. Clasifica topics del contexto
  2. Llama a retrieval especializado por tipo de Guardian
  3. Pasa resultados filtrados al agente

**Mapeo categoría → Guardian:**
- `mind` → `retrieve_for_mental()`
- `body` → `retrieve_for_physical()`
- `soul` → `retrieve_for_spiritual()`
- `holistic` → búsqueda general sin filtros

## Flujo de Datos

```
User Request
    ↓
HolisticAdviceService.generate_advice()
    ↓
1. Clasificar contexto → TopicClassifier
    ↓
2. Seleccionar Guardian (mind/body/soul)
    ↓
3. GuardianKnowledgeRetriever.retrieve_for_X()
    ↓
4. Filtrar topics por dominio del Guardian
    ↓
5. Construir VectorSearchFilters
    ↓
6. VectorQueryRunner.run(filters=...)
    ↓
7. Qdrant search con filtros
    ↓
8. Aplicar boosting (abstracts + recientes)
    ↓
9. Retornar resultados a agente Guardian
    ↓
Agent execution con knowledge_context filtrado
```

## Ejemplos de Uso

### Ejemplo 1: Mental Guardian con problemas de estrés
```python
context = "Estoy muy estresado y ansioso últimamente"

# 1. Clasificación de topics
topics = classifier.classify(context)
# → ["mental_health", "stress_response"]

# 2. Retrieval especializado
results = retriever.retrieve_for_mental(
    trace_id="123",
    context=context,
    user_topics=topics
)

# 3. Filtros aplicados:
# - category: "mente"
# - topics: ["mental_health", "stress_response"] (ambos en dominio mental)
# - boost_abstracts: True
# - boost_recent: True

# 4. Documentos retornados: solo de categoría "mente" y topics mentales
```

### Ejemplo 2: Physical Guardian con problemas de sueño
```python
context = "Tengo problemas para dormir, me despierto a las 3am"

# 1. Clasificación
topics = classifier.classify(context)
# → ["sleep_health", "insomnia", "circadian_rhythm"]

# 2. Retrieval especializado
results = retriever.retrieve_for_physical(
    trace_id="456",
    context=context,
    user_topics=topics
)

# 3. Filtros aplicados:
# - category: "cuerpo"
# - topics: ["sleep_health", "insomnia", "circadian_rhythm"] (todos en dominio physical)
# - boost_abstracts: True
# - boost_recent: True

# 4. Documentos retornados:
# - Solo papers de categoría "cuerpo"
# - Solo papers con topics de sueño
# - Abstracts tienen mayor score
# - Papers recientes (2020+) tienen mayor score
```

### Ejemplo 3: Spiritual Guardian con búsqueda de propósito
```python
context = "Siento que me falta un propósito claro en la vida"

# 1. Clasificación
topics = classifier.classify(context)
# → ["mental_health", "stress_response", "aging_longevity"]

# 2. Retrieval especializado
results = retriever.retrieve_for_spiritual(
    trace_id="789",
    context=context,
    user_topics=topics
)

# 3. Filtros aplicados:
# - category: "alma"
# - topics: ["mental_health", "stress_response", "aging_longevity"]
#   (todos están en dominio spiritual)

# 4. Documentos retornados: solo de categoría "alma" con topics espirituales
```

## Testing

### Tests Unitarios
**Ubicación:** `tests/unit/test_topic_classifier.py`

Cobertura:
- Clasificación de contexto (texto y dict)
- Filtrado de topics inválidos
- Manejo de errores JSON
- Limpieza de markdown code blocks
- Fallback por keywords
- Cache de clasificaciones

**Ejecutar:**
```bash
cd services/agents
uv run pytest tests/unit/test_topic_classifier.py -v
```

### Tests de Integración
**Ubicación:** `tests/integration/test_guardian_routing.py`

Cobertura:
- Retrieval especializado por cada Guardian
- Filtrado correcto de topics por dominio
- Construcción de filtros Qdrant
- Manejo de casos sin topics relevantes
- Fallback en caso de errores
- Separación correcta de dominios

**Ejecutar:**
```bash
cd services/agents
uv run pytest tests/integration/test_guardian_routing.py -v
```

### Script de Validación
**Ubicación:** `scripts/test_guardian_routing.py`

Valida el sistema completo end-to-end:
1. Clasificación de topics con casos reales
2. Routing correcto a cada Guardian
3. Boosting de metadata funcionando

**Ejecutar:**
```bash
cd services/agents
./scripts/test_guardian_routing.py
```

**Salida esperada:**
```
VALIDACIÓN DE GUARDIAN ROUTING ESPECIALIZADO
================================================================================

VALIDANDO CLASIFICACIÓN DE TOPICS
  ✅ Topics clasificados: ['mental_health', 'stress_response']
  ✅ Al menos un topic esperado encontrado

VALIDANDO ROUTING POR GUARDIAN
  🧠 Guardian: MENTAL
  ✅ Documentos encontrados: 5
  📊 Confidence score: 0.8234
  🔧 Filtros aplicados:
     - Categoría: mente
     - Topics: ['mental_health', 'stress_response']

VALIDANDO BOOSTING DE METADATA
  📊 Estadísticas de boosting:
   - Documentos con boost: 8/10
   - Abstracts/Conclusions: 4
   - Papers recientes (2020+): 6
   ✅ Boosting funcionando correctamente

RESUMEN DE VALIDACIÓN
✅ Clasificación de topics: PASSED
✅ Routing por Guardian: PASSED
✅ Boosting de metadata: PASSED

🎉 Todas las validaciones pasaron correctamente!
```

## Configuración

### Variables de Entorno Necesarias

```bash
# En services/agents/.env

# Gemini API Key (para clasificación de topics)
GOOGLE_API_KEY=your_gemini_api_key

# Qdrant (ya configurado)
AGENT_SERVICE_QDRANT_URL=http://localhost:6333
AGENT_SERVICE_VECTOR_COLLECTION=holistic_agents
AGENT_SERVICE_VECTOR_TOP_K=5

# Embeddings (ya configurado)
AGENT_DEFAULT_EMBEDDING_MODEL=text-embedding-3-small
AGENT_SERVICE_EMBEDDING_BACKEND=gemini
```

### Dependencias Nuevas

Ninguna! Usa las dependencias existentes:
- `google-generativeai` (ya instalado para ADK)
- `qdrant-client` (ya instalado)

## Performance

### Latencias Esperadas

**Clasificación de topics:**
- Con Gemini 2.0 Flash: ~200-500ms
- Con cache hit: ~0ms

**Búsqueda vectorial con filtros:**
- Embedding generation: ~100ms (con cache Redis: ~10ms)
- Qdrant search con filtros: ~50-150ms
- Boosting post-procesamiento: ~1ms

**Total por request:**
- Primera vez (sin cache): ~350-750ms
- Con cache: ~60-200ms

### Optimizaciones Implementadas

1. **Cache de clasificaciones:** Evita llamadas repetidas a Gemini
2. **Cache de embeddings:** Redis en vectordb (90% speedup)
3. **Filtrado en Qdrant:** Reduce set de documentos antes de calcular scores
4. **Boosting en memoria:** Más rápido que re-queries a Qdrant

## Troubleshooting

### Problema: No se encuentran documentos relevantes

**Causa:** Topics del usuario no coinciden con dominio del Guardian

**Solución:** El sistema aplica fallback automático:
1. Intenta con todos los topics del dominio del Guardian
2. Si falla, intenta sin filtros de topics (solo categoría)
3. Si falla, retorna lista vacía

**Log esperado:**
```
GuardianRetrieval[mental]: Sin topics relevantes en el dominio.
GuardianRetrieval[mental]: Usando dominio completo como fallback.
GuardianRetrieval[mental]: Intentando fallback sin filtros de topics
```

### Problema: Clasificación de topics incorrecta

**Causa:** Contexto del usuario ambiguo o fuera de dominios biomédicos

**Solución:**
1. Verificar prompt en `CLASSIFICATION_PROMPT`
2. Ajustar temperatura del modelo (actualmente 0.1)
3. Agregar más descripciones en `TOPIC_DESCRIPTIONS`
4. Mejorar fallback keywords en `_get_fallback_topics()`

### Problema: Boosting no se aplica

**Causa:** Metadata faltante en documentos de Qdrant

**Verificar:**
```python
# En vectordb, verificar que los chunks tienen:
{
    "is_abstract": bool,
    "is_conclusion": bool,
    "year": int,
    "topics": list[str]
}
```

**Solución:** Re-ingestar documentos con pipeline actualizado

## Roadmap Futuro

### Mejoras Potenciales

1. **Multi-stage retrieval:**
   - Stage 1: Búsqueda amplia con categoría
   - Stage 2: Re-rank por topic relevance
   - Stage 3: Diversificación de resultados

2. **Hybrid search:**
   - Combinar dense (embeddings) + sparse (BM25)
   - Fusion de scores

3. **Context persistence:**
   - Guardar historial de conversación
   - Construir embeddings personalizados por usuario
   - Long-term memory integration

4. **A/B testing:**
   - Comparar resultados con/sin filtros
   - Medir calidad de respuestas de Guardians
   - Optimizar pesos de boosting

5. **Topic expansion:**
   - Agregar sinónimos de topics
   - Expandir queries con embeddings de topics relacionados

## Referencias

- **Topics biomédicos:** `services/vectordb/config/topics.yaml`
- **Dominios de Guardians:** `services/agents/infra/settings.py:154`
- **Clasificador LLM:** `services/agents/services/topic_classifier.py`
- **Guardian retrieval:** `services/agents/services/guardian_retrieval.py`
- **Vector queries:** `services/agents/services/vector_queries.py`
- **Orchestration:** `services/agents/services/holistic.py`

## Métricas de Éxito

### KPIs a Monitorear

1. **Precision@K:** % de documentos relevantes en top-K
2. **Topic classification accuracy:** % de topics correctamente clasificados
3. **Retrieval latency:** Tiempo total de búsqueda (target: <500ms)
4. **Cache hit rate:** % de requests que usan cache (target: >70%)
5. **Guardian specialization score:** % de documentos del dominio correcto

### Logging

Todos los componentes loggean:
- Topics clasificados por request
- Filtros aplicados en búsqueda
- Número de documentos retornados
- Scores y boost aplicados
- Fallbacks activados

**Ver logs:**
```bash
cd services/agents
uv run uvicorn main:app --reload --log-level info
```

## Contribuciones

Para agregar nuevos topics o modificar dominios:

1. Actualizar `services/vectordb/config/topics.yaml`
2. Actualizar `AVAILABLE_TOPICS` en `services/topic_classifier.py`
3. Actualizar `TOPIC_DESCRIPTIONS` con descripciones en español
4. Actualizar `GUARDIAN_KNOWLEDGE_DOMAINS` en `services/agents/infra/settings.py`
5. Ejecutar tests de validación
6. Re-ingestar documentos en vectordb con nuevos topics

---

**Fecha de implementación:** 2025-05-11
**Versión:** 1.0.0
**Estado:** ✅ Producción ready
