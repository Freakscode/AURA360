"""
Celery Tasks para Procesamiento de Mediciones Corporales

Tareas asíncronas para:
1. Cálculo automático de composición corporal
2. Vectorización de mediciones para RAG
3. Análisis de tendencias (Fase 2)
"""

import json
import os
from typing import Dict, Any, Optional, List
from loguru import logger
from celery import shared_task

# Importar módulos propios
from vectosvc.core.anthropometry import calculate_all_metrics
from vectosvc.core.embeddings import Embeddings
from vectosvc.config import settings


# ============================================================================
# TASK 1: CALCULATE BODY COMPOSITION
# ============================================================================

@shared_task(
    name='calculate_body_composition',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def calculate_body_composition(
    self,
    measurement_id: str,
    measurement_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calcula automáticamente todos los campos derivados de una medición corporal.

    Esta tarea se ejecuta después de crear/actualizar un BodyMeasurement.

    Args:
        measurement_id: UUID de la medición
        measurement_data: Dict con todos los campos de la medición:
            - weight_kg: float (requerido)
            - height_cm: float (opcional)
            - age: int (requerido para % grasa)
            - gender: str ('M' o 'F', requerido para % grasa)
            - *_skinfold_mm: pliegues opcionales
            - *_circumference_cm: circunferencias opcionales
            - *_breadth_mm: diámetros opcionales

    Returns:
        Dict con campos calculados:
            - bmi: float
            - body_fat_percentage: float
            - fat_mass_kg: float
            - muscle_mass_kg: float
            - muscle_mass_percentage: float
            - endomorphy: float
            - mesomorphy: float
            - ectomorphy: float
            - waist_hip_ratio: float
            - waist_height_ratio: float
            - cardiovascular_risk: str

    Raises:
        Exception: Si el cálculo falla (se reintenta automáticamente)

    Example:
        >>> from vectosvc.worker.body_tasks import calculate_body_composition
        >>> result = calculate_body_composition.delay(
        ...     measurement_id="uuid-here",
        ...     measurement_data={
        ...         'weight_kg': 75.0,
        ...         'height_cm': 175.0,
        ...         'age': 30,
        ...         'gender': 'M',
        ...         # ... más campos
        ...     }
        ... )
        >>> result.get(timeout=10)
        {'bmi': 24.49, 'body_fat_percentage': 12.5, ...}
    """
    try:
        logger.info(
            f"📊 Calculating body composition for measurement {measurement_id}"
        )

        # Validar datos mínimos
        if not measurement_data.get('weight_kg'):
            raise ValueError("weight_kg is required")

        # Calcular todas las métricas
        calculated_metrics = calculate_all_metrics(measurement_data)

        if not calculated_metrics:
            raise ValueError("No metrics could be calculated")

        logger.success(
            f"✅ Body composition calculated for {measurement_id}: "
            f"BMI={calculated_metrics.get('bmi')}, "
            f"BF%={calculated_metrics.get('body_fat_percentage')}"
        )

        # Retornar para que Django API actualice el modelo
        return {
            'measurement_id': measurement_id,
            'status': 'success',
            'calculated_fields': calculated_metrics,
            'fields_calculated': list(calculated_metrics.keys())
        }

    except Exception as e:
        logger.error(
            f"❌ Failed to calculate body composition for {measurement_id}: {e}",
            exc_info=True
        )

        # Retry automático (máx 3 intentos)
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for measurement {measurement_id}")
            return {
                'measurement_id': measurement_id,
                'status': 'failed',
                'error': str(e),
                'calculated_fields': {}
            }


# ============================================================================
# TASK 2: VECTORIZE BODY MEASUREMENT
# ============================================================================

@shared_task(
    name='vectorize_body_measurement',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def vectorize_body_measurement(
    self,
    measurement_id: str,
    auth_user_id: str,
    measurement_summary: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Vectoriza una medición corporal para indexación semántica en Qdrant.

    Permite búsquedas como:
    - "Pacientes con alto % de grasa corporal"
    - "Deportistas con somatotipo mesomorfo"
    - "Historial de composición corporal del paciente X"

    Args:
        measurement_id: UUID de la medición
        auth_user_id: UUID del usuario/paciente
        measurement_summary: Dict con datos de la medición:
            - recorded_at: str (ISO date)
            - protocol: str (isak_restricted, clinical_basic, etc.)
            - patient_type: str (sedentary, active, athlete, etc.)
            - weight_kg: float
            - height_cm: float
            - bmi: float
            - body_fat_percentage: float
            - muscle_mass_kg: float
            - endomorphy: float
            - mesomorphy: float
            - ectomorphy: float
            - waist_hip_ratio: float
            - cardiovascular_risk: str

    Returns:
        Dict con resultado:
            - measurement_id: str
            - vector_id: str (ID en Qdrant)
            - status: 'success' o 'failed'

    Example:
        >>> result = vectorize_body_measurement.delay(
        ...     measurement_id="uuid-here",
        ...     auth_user_id="user-uuid",
        ...     measurement_summary={...}
        ... )
    """
    try:
        logger.info(
            f"🔍 Vectorizing body measurement {measurement_id} for user {auth_user_id}"
        )

        # Generar texto contextual para embedding
        context_text = _build_measurement_context(measurement_summary)

        if not context_text:
            raise ValueError("Could not generate context text")

        logger.debug(f"Generated context text: {context_text[:200]}...")

        # Generar embedding
        embeddings_service = Embeddings()
        embedding_vector = embeddings_service.encode([context_text])[0]

        # Preparar metadata para Qdrant
        metadata = {
            'measurement_id': measurement_id,
            'auth_user_id': auth_user_id,
            'recorded_at': measurement_summary.get('recorded_at'),
            'protocol': measurement_summary.get('protocol', 'unknown'),
            'patient_type': measurement_summary.get('patient_type', 'unknown'),
            'bmi': measurement_summary.get('bmi'),
            'body_fat_percentage': measurement_summary.get('body_fat_percentage'),
            'cardiovascular_risk': measurement_summary.get('cardiovascular_risk', 'unknown'),
            'data_type': 'body_measurement',
            'text_preview': context_text[:200]
        }

        # Almacenar en Qdrant
        from vectosvc.core.qdrant_store import store
        from qdrant_client.models import PointStruct
        import uuid

        vector_id = str(uuid.uuid4())

        store.upsert(
            collection_name=settings.collection_name,  # holistic_memory
            points=[
                PointStruct(
                    id=vector_id,
                    vector=embedding_vector.tolist(),
                    payload=metadata
                )
            ]
        )

        logger.success(
            f"✅ Measurement {measurement_id} vectorized successfully: vector_id={vector_id}"
        )

        return {
            'measurement_id': measurement_id,
            'vector_id': vector_id,
            'status': 'success',
            'collection': settings.collection_name
        }

    except Exception as e:
        logger.error(
            f"❌ Failed to vectorize measurement {measurement_id}: {e}",
            exc_info=True
        )

        # Retry automático
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for vectorizing {measurement_id}")
            return {
                'measurement_id': measurement_id,
                'status': 'failed',
                'error': str(e)
            }


# ============================================================================
# TASK 3: ANALYZE PROGRESS TRENDS (Fase 2)
# ============================================================================

@shared_task(
    name='analyze_progress_trends',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def analyze_progress_trends(
    self,
    auth_user_id: str,
    time_range_days: Optional[int] = None,
    target_metrics: Optional[list] = None
) -> Dict[str, Any]:
    """
    Analiza tendencias de progreso en mediciones corporales de un usuario.

    Esta tarea procesa series temporales de mediciones y detecta:
    - Tendencias lineales (aumento/disminución/estable)
    - Velocidades de cambio (kg/semana, %/mes)
    - Significancia estadística (p-value, R²)
    - Proyecciones a 30 días
    - Alertas sobre cambios rápidos o preocupantes

    Args:
        auth_user_id: UUID del usuario/paciente
        time_range_days: Rango temporal en días (None = todas las mediciones)
        target_metrics: Lista de métricas a analizar (None = todas)

    Returns:
        Dict con análisis completo:
        {
            'user_id': str,
            'analysis': {
                'period': {'start': str, 'end': str, 'days': int},
                'measurement_count': int,
                'trends': {
                    'weight_kg': {
                        'direction': 'increasing' | 'decreasing' | 'stable',
                        'slope': float,
                        'change_total': float,
                        'change_percent': float,
                        'velocity_per_week': float,
                        'velocity_per_month': float,
                        'significance': str,
                        'p_value': float,
                        'r_squared': float,
                        'projection_30d': float
                    },
                    ...
                },
                'alerts': [
                    {
                        'metric': str,
                        'level': 'info' | 'warning' | 'critical',
                        'message': str,
                        'recommendation': str
                    }
                ],
                'summary': str
            },
            'status': 'success' | 'failed'
        }

    Example:
        >>> from vectosvc.worker.body_tasks import analyze_progress_trends
        >>> result = analyze_progress_trends.delay(
        ...     auth_user_id="user-uuid-here",
        ...     time_range_days=90,
        ...     target_metrics=['weight_kg', 'body_fat_percentage']
        ... )
        >>> analysis = result.get(timeout=30)
        >>> print(analysis['analysis']['summary'])
    """
    try:
        logger.info(
            f"📈 Analyzing progress trends for user {auth_user_id} "
            f"(range: {time_range_days or 'all'} days)"
        )

        # Obtener mediciones del usuario desde Django API
        measurements = _fetch_user_measurements(auth_user_id, time_range_days)

        if not measurements:
            logger.warning(f"No measurements found for user {auth_user_id}")
            return {
                'user_id': auth_user_id,
                'status': 'success',
                'analysis': {
                    'period': None,
                    'measurement_count': 0,
                    'trends': {},
                    'alerts': [{
                        'metric': 'general',
                        'level': 'info',
                        'message': 'No hay mediciones registradas.',
                        'recommendation': 'Registra tu primera medición para comenzar el seguimiento.'
                    }],
                    'summary': 'Sin datos disponibles.'
                }
            }

        # Analizar tendencias usando el módulo trends
        from vectosvc.core.trends import analyze_measurement_trends

        analysis = analyze_measurement_trends(
            measurements=measurements,
            time_range_days=time_range_days,
            target_metrics=target_metrics
        )

        logger.success(
            f"✅ Trends analyzed for user {auth_user_id}: "
            f"{analysis['measurement_count']} measurements, "
            f"{len(analysis['trends'])} metrics, "
            f"{len(analysis['alerts'])} alerts"
        )

        return {
            'user_id': auth_user_id,
            'status': 'success',
            'analysis': analysis
        }

    except Exception as e:
        logger.error(
            f"❌ Failed to analyze trends for user {auth_user_id}: {e}",
            exc_info=True
        )

        # Retry automático
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for trend analysis {auth_user_id}")
            return {
                'user_id': auth_user_id,
                'status': 'failed',
                'error': str(e),
                'analysis': None
            }


def _fetch_user_measurements(
    auth_user_id: str,
    time_range_days: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene las mediciones de un usuario desde Django API.

    Args:
        auth_user_id: UUID del usuario
        time_range_days: Rango temporal opcional

    Returns:
        Lista de mediciones ordenadas por fecha (más reciente primero)
    """
    try:
        # Intentar obtener desde Django ORM directamente
        from body.models import BodyMeasurement
        from datetime import datetime, timedelta

        queryset = BodyMeasurement.objects.filter(
            auth_user_id=auth_user_id
        ).order_by('-recorded_at')

        if time_range_days:
            cutoff_date = datetime.now() - timedelta(days=time_range_days)
            queryset = queryset.filter(recorded_at__gte=cutoff_date)

        # Convertir a diccionarios
        measurements = []
        for measurement in queryset:
            measurements.append({
                'id': str(measurement.id),
                'recorded_at': measurement.recorded_at.isoformat() if measurement.recorded_at else None,
                'weight_kg': float(measurement.weight_kg) if measurement.weight_kg else None,
                'height_cm': float(measurement.height_cm) if measurement.height_cm else None,
                'bmi': float(measurement.bmi) if measurement.bmi else None,
                'body_fat_percentage': float(measurement.body_fat_percentage) if measurement.body_fat_percentage else None,
                'fat_mass_kg': float(measurement.fat_mass_kg) if measurement.fat_mass_kg else None,
                'muscle_mass_kg': float(measurement.muscle_mass_kg) if measurement.muscle_mass_kg else None,
                'waist_circumference_cm': float(measurement.waist_circumference_cm) if measurement.waist_circumference_cm else None,
                'hip_circumference_cm': float(measurement.hip_circumference_cm) if measurement.hip_circumference_cm else None,
                'waist_hip_ratio': float(measurement.waist_hip_ratio) if measurement.waist_hip_ratio else None,
                'waist_height_ratio': float(measurement.waist_height_ratio) if measurement.waist_height_ratio else None,
                'cardiovascular_risk': measurement.cardiovascular_risk
            })

        return measurements

    except ImportError:
        # Si no está disponible Django ORM, intentar via HTTP API
        logger.warning("Django ORM not available, falling back to HTTP API")
        return _fetch_measurements_via_http(auth_user_id, time_range_days)
    except Exception as e:
        logger.error(f"Failed to fetch measurements for {auth_user_id}: {e}")
        return []


def _fetch_measurements_via_http(
    auth_user_id: str,
    time_range_days: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene mediciones via HTTP API (fallback).

    Args:
        auth_user_id: UUID del usuario
        time_range_days: Rango temporal opcional

    Returns:
        Lista de mediciones
    """
    import requests

    try:
        api_url = os.getenv('DJANGO_API_URL', 'http://localhost:8000')
        endpoint = f"{api_url}/api/body/measurements/"

        params = {
            'auth_user_id': auth_user_id,
            'ordering': '-recorded_at'
        }

        if time_range_days:
            params['days_back'] = time_range_days

        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()

        return response.json().get('results', [])

    except Exception as e:
        logger.error(f"Failed to fetch measurements via HTTP: {e}")
        return []


# ============================================================================
# TASK 4: ANALYZE NUTRITION ADHERENCE (Fase 4)
# ============================================================================

@shared_task(
    name='analyze_nutrition_adherence',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def analyze_nutrition_adherence(
    self,
    auth_user_id: str,
    nutrition_plan_id: str,
    time_range_days: Optional[int] = 7
) -> Dict[str, Any]:
    """
    Analiza la adherencia de un usuario a su plan nutricional.

    Compara el plan nutricional prescrito con los registros reales de consumo
    para detectar patrones de cumplimiento, problemas y tendencias.

    Args:
        auth_user_id: UUID del usuario/paciente
        nutrition_plan_id: UUID del plan nutricional a analizar
        time_range_days: Días a analizar (default: última semana)

    Returns:
        Dict con análisis completo:
        {
            'user_id': str,
            'plan_id': str,
            'status': 'success' | 'failed',
            'analysis': {
                'adherence_level': str,
                'adherence_rates': {...},
                'issues': [...],
                'trends': {...},
                'summary': str
            }
        }

    Example:
        >>> from vectosvc.worker.body_tasks import analyze_nutrition_adherence
        >>> result = analyze_nutrition_adherence.delay(
        ...     auth_user_id="user-uuid",
        ...     nutrition_plan_id="plan-uuid",
        ...     time_range_days=7
        ... )
        >>> analysis = result.get(timeout=30)
    """
    try:
        logger.info(
            f"🍽️ Analyzing nutrition adherence for user {auth_user_id}, plan {nutrition_plan_id}"
        )

        # Obtener plan nutricional
        nutrition_plan = _fetch_nutrition_plan(auth_user_id, nutrition_plan_id)
        if not nutrition_plan:
            return {
                'user_id': auth_user_id,
                'plan_id': nutrition_plan_id,
                'status': 'failed',
                'error': 'Nutrition plan not found',
                'analysis': None
            }

        # Obtener registros de nutrición
        nutrition_logs = _fetch_nutrition_logs(auth_user_id, time_range_days)

        # Analizar adherencia
        from vectosvc.core.nutrition_adherence import analyze_nutrition_adherence as analyze

        analysis = analyze(
            nutrition_plan=nutrition_plan,
            nutrition_logs=nutrition_logs,
            time_range_days=time_range_days
        )

        logger.success(
            f"✅ Adherence analyzed for user {auth_user_id}: "
            f"{analysis['adherence_level']} ({analysis['adherence_rates']['overall']:.1f}%)"
        )

        return {
            'user_id': auth_user_id,
            'plan_id': nutrition_plan_id,
            'status': 'success',
            'analysis': analysis
        }

    except Exception as e:
        logger.error(
            f"❌ Failed to analyze adherence for user {auth_user_id}: {e}",
            exc_info=True
        )

        # Retry automático
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for adherence analysis {auth_user_id}")
            return {
                'user_id': auth_user_id,
                'plan_id': nutrition_plan_id,
                'status': 'failed',
                'error': str(e),
                'analysis': None
            }


# ============================================================================
# TASK 5: GENERATE AI RECOMMENDATIONS (Fase 4)
# ============================================================================

@shared_task(
    name='generate_ai_recommendations',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def generate_ai_recommendations(
    self,
    auth_user_id: str,
    include_trends: bool = True,
    include_adherence: bool = True,
    time_range_days: int = 30
) -> Dict[str, Any]:
    """
    Genera recomendaciones personalizadas usando IA (LLM).

    Integra múltiples fuentes de datos para generar recomendaciones
    accionables y personalizadas:
    - Tendencias de progreso corporal
    - Adherencia nutricional
    - Mediciones antropométricas actuales
    - Objetivos del usuario

    Args:
        auth_user_id: UUID del usuario/paciente
        include_trends: Incluir análisis de tendencias
        include_adherence: Incluir análisis de adherencia
        time_range_days: Días de historia a considerar

    Returns:
        Dict con recomendaciones:
        {
            'user_id': str,
            'status': 'success' | 'failed',
            'recommendations': [
                {
                    'type': str,
                    'priority': str,
                    'title': str,
                    'description': str,
                    'rationale': str,
                    'action_steps': List[str]
                }
            ],
            'overall_assessment': str,
            'key_focus_areas': List[str]
        }

    Example:
        >>> from vectosvc.worker.body_tasks import generate_ai_recommendations
        >>> result = generate_ai_recommendations.delay(
        ...     auth_user_id="user-uuid",
        ...     include_trends=True,
        ...     include_adherence=True
        ... )
        >>> recommendations = result.get(timeout=60)
    """
    try:
        logger.info(
            f"🤖 Generating AI recommendations for user {auth_user_id}"
        )

        # Obtener datos del usuario
        user_data = _fetch_user_data(auth_user_id)

        # Obtener última medición
        latest_measurement = _fetch_latest_measurement(auth_user_id)

        # Obtener análisis de tendencias si se solicita
        trends = None
        if include_trends:
            try:
                # Llamar a la tarea de tendencias (síncronamente)
                trends_result = analyze_progress_trends(
                    auth_user_id=auth_user_id,
                    time_range_days=time_range_days,
                    target_metrics=None
                )
                if trends_result['status'] == 'success':
                    trends = trends_result['analysis']
            except Exception as e:
                logger.warning(f"Could not get trends for recommendations: {e}")

        # Obtener análisis de adherencia si se solicita
        adherence = None
        if include_adherence:
            try:
                # Obtener plan activo del usuario
                active_plan = _fetch_active_nutrition_plan(auth_user_id)
                if active_plan:
                    adherence_result = analyze_nutrition_adherence(
                        auth_user_id=auth_user_id,
                        nutrition_plan_id=active_plan['id'],
                        time_range_days=min(time_range_days, 14)  # Máximo 2 semanas
                    )
                    if adherence_result['status'] == 'success':
                        adherence = adherence_result['analysis']
            except Exception as e:
                logger.warning(f"Could not get adherence for recommendations: {e}")

        # Generar recomendaciones con IA
        from vectosvc.core.ai_recommendations import generate_ai_recommendations as generate

        recommendations_data = generate(
            user_id=auth_user_id,
            user_data=user_data,
            trends=trends,
            adherence=adherence,
            latest_measurement=latest_measurement
        )

        logger.success(
            f"✅ Generated {len(recommendations_data['recommendations'])} recommendations "
            f"for user {auth_user_id}"
        )

        return {
            'user_id': auth_user_id,
            'status': 'success',
            **recommendations_data
        }

    except Exception as e:
        logger.error(
            f"❌ Failed to generate AI recommendations for user {auth_user_id}: {e}",
            exc_info=True
        )

        # Retry automático
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for AI recommendations {auth_user_id}")
            return {
                'user_id': auth_user_id,
                'status': 'failed',
                'error': str(e),
                'recommendations': [],
                'overall_assessment': '',
                'key_focus_areas': []
            }


# ============================================================================
# HELPER FUNCTIONS (Fetch Data from Django)
# ============================================================================

def _fetch_nutrition_plan(auth_user_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene un plan nutricional desde Django ORM."""
    try:
        from body.models import NutritionPlan

        plan = NutritionPlan.objects.get(id=plan_id, auth_user_id=auth_user_id)

        return {
            'id': str(plan.id),
            'title': plan.title,
            'plan_data': plan.plan_data,
            'daily_calories': plan.plan_data.get('nutrition', {}).get('daily_calories'),
            'daily_protein_g': plan.plan_data.get('nutrition', {}).get('daily_protein_g'),
            'daily_carbs_g': plan.plan_data.get('nutrition', {}).get('daily_carbs_g'),
            'daily_fats_g': plan.plan_data.get('nutrition', {}).get('daily_fats_g')
        }

    except ImportError:
        logger.warning("Django ORM not available")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch nutrition plan: {e}")
        return None


def _fetch_nutrition_logs(
    auth_user_id: str,
    days: int = 7
) -> List[Dict[str, Any]]:
    """Obtiene registros de nutrición desde Django ORM."""
    try:
        from body.models import NutritionLog
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        logs = NutritionLog.objects.filter(
            auth_user_id=auth_user_id,
            logged_at__gte=cutoff_date
        ).order_by('-logged_at')

        return [
            {
                'id': str(log.id),
                'logged_at': log.logged_at.isoformat() if log.logged_at else None,
                'total_calories': float(log.total_calories) if log.total_calories else 0,
                'total_protein_g': float(log.total_protein_g) if log.total_protein_g else 0,
                'total_carbs_g': float(log.total_carbs_g) if log.total_carbs_g else 0,
                'total_fats_g': float(log.total_fats_g) if log.total_fats_g else 0,
                'meal_type': log.meal_type
            }
            for log in logs
        ]

    except ImportError:
        logger.warning("Django ORM not available")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch nutrition logs: {e}")
        return []


def _fetch_user_data(auth_user_id: str) -> Dict[str, Any]:
    """Obtiene datos demográficos del usuario."""
    # TODO: Implementar obtención real desde users table
    return {
        'age': 30,  # Placeholder
        'gender': 'M',  # Placeholder
        'patient_type': 'active',  # Placeholder
        'goal': 'weight_loss'  # Placeholder
    }


def _fetch_latest_measurement(auth_user_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene la última medición corporal del usuario."""
    try:
        from body.models import BodyMeasurement

        measurement = BodyMeasurement.objects.filter(
            auth_user_id=auth_user_id
        ).order_by('-recorded_at').first()

        if not measurement:
            return None

        return {
            'id': str(measurement.id),
            'recorded_at': measurement.recorded_at.isoformat() if measurement.recorded_at else None,
            'weight_kg': float(measurement.weight_kg) if measurement.weight_kg else None,
            'height_cm': float(measurement.height_cm) if measurement.height_cm else None,
            'bmi': float(measurement.bmi) if measurement.bmi else None,
            'body_fat_percentage': float(measurement.body_fat_percentage) if measurement.body_fat_percentage else None,
            'muscle_mass_kg': float(measurement.muscle_mass_kg) if measurement.muscle_mass_kg else None,
            'cardiovascular_risk': measurement.cardiovascular_risk
        }

    except ImportError:
        return None
    except Exception as e:
        logger.error(f"Failed to fetch latest measurement: {e}")
        return None


def _fetch_active_nutrition_plan(auth_user_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene el plan nutricional activo del usuario."""
    try:
        from body.models import NutritionPlan

        plan = NutritionPlan.objects.filter(
            auth_user_id=auth_user_id,
            is_active=True
        ).order_by('-created_at').first()

        if not plan:
            return None

        return {
            'id': str(plan.id),
            'title': plan.title
        }

    except ImportError:
        return None
    except Exception as e:
        logger.error(f"Failed to fetch active nutrition plan: {e}")
        return None


def _build_measurement_context(measurement: Dict[str, Any]) -> str:
    """
    Construye texto contextual para embedding de una medición.

    Args:
        measurement: Dict con datos de la medición

    Returns:
        Texto descriptivo de la medición
    """
    lines = []

    # Contexto básico
    protocol = measurement.get('protocol', 'clinical_basic')
    patient_type = measurement.get('patient_type', 'unknown')
    recorded_at = measurement.get('recorded_at', 'unknown date')

    protocol_names = {
        'isak_restricted': 'Protocolo ISAK Restringido',
        'isak_full': 'Protocolo ISAK Completo',
        'clinical_basic': 'Evaluación Clínica Básica',
        'elderly_sarcopenia': 'Evaluación Adulto Mayor (Sarcopenia)',
        'self_reported': 'Auto-reportado'
    }

    patient_type_names = {
        'sedentary': 'sedentario',
        'active': 'activo',
        'athlete': 'deportista',
        'elderly': 'adulto mayor',
        'child': 'niño/adolescente'
    }

    lines.append(f"Medición antropométrica realizada el {recorded_at}.")
    lines.append(f"{protocol_names.get(protocol, protocol)} aplicado.")
    lines.append(f"Tipo de paciente: {patient_type_names.get(patient_type, patient_type)}.")

    # Medidas básicas
    weight = measurement.get('weight_kg')
    height = measurement.get('height_cm')
    bmi = measurement.get('bmi')

    if weight:
        lines.append(f"Peso corporal: {weight} kg.")

    if height:
        lines.append(f"Estatura: {height} cm.")

    if bmi:
        bmi_cat = _get_bmi_category_text(bmi)
        lines.append(f"IMC: {bmi} ({bmi_cat}).")

    # Composición corporal
    bf_pct = measurement.get('body_fat_percentage')
    muscle_kg = measurement.get('muscle_mass_kg')

    if bf_pct is not None:
        lines.append(f"Porcentaje de grasa corporal: {bf_pct}%.")

    if muscle_kg:
        lines.append(f"Masa muscular estimada: {muscle_kg} kg.")

    # Somatotipo
    endo = measurement.get('endomorphy')
    meso = measurement.get('mesomorphy')
    ecto = measurement.get('ectomorphy')

    if all([endo, meso, ecto]):
        somato_type = _classify_somatotype(endo, meso, ecto)
        lines.append(
            f"Somatotipo Heath-Carter: {endo}-{meso}-{ecto} ({somato_type})."
        )

    # Índices de salud
    whr = measurement.get('waist_hip_ratio')
    whtr = measurement.get('waist_height_ratio')
    cv_risk = measurement.get('cardiovascular_risk')

    if whr:
        lines.append(f"Índice Cintura-Cadera (ICC): {whr}.")

    if whtr:
        risk_text = "saludable" if whtr < 0.5 else "precaución" if whtr < 0.6 else "riesgo"
        lines.append(f"Índice Cintura-Estatura (ICE): {whtr} ({risk_text}).")

    if cv_risk:
        risk_names = {
            'low': 'bajo',
            'moderate': 'moderado',
            'high': 'alto',
            'very_high': 'muy alto'
        }
        lines.append(
            f"Riesgo cardiovascular: {risk_names.get(cv_risk, cv_risk)}."
        )

    return " ".join(lines)


def _get_bmi_category_text(bmi: float) -> str:
    """Convierte BMI a categoría en español."""
    if bmi < 18.5:
        return "bajo peso"
    elif bmi < 25.0:
        return "peso normal"
    elif bmi < 30.0:
        return "sobrepeso"
    elif bmi < 35.0:
        return "obesidad grado 1"
    elif bmi < 40.0:
        return "obesidad grado 2"
    else:
        return "obesidad grado 3"


def _classify_somatotype(endo: float, meso: float, ecto: float) -> str:
    """
    Clasifica el somatotipo según los componentes dominantes.

    Returns:
        Texto descriptivo del somatotipo
    """
    # Encontrar el componente dominante
    components = {'endomorfo': endo, 'mesomorfo': meso, 'ectomorfo': ecto}
    dominant = max(components, key=components.get)

    # Verificar si es balanceado (ninguno domina claramente)
    values = [endo, meso, ecto]
    max_val = max(values)
    min_val = min(values)

    if max_val - min_val < 1.5:
        return "balanceado"

    # Verificar combinaciones
    if endo > 5 and meso > 5:
        return "endomesomorfo"
    elif meso > 5 and ecto > 5:
        return "mesoectomorfo"
    elif endo > 5 and ecto > 5:
        return "endoectomorfo (raro)"

    return dominant


# ============================================================================
# HELPER: UPDATE DJANGO MODEL (called from Django API)
# ============================================================================

def update_measurement_with_calculations(
    measurement_id: str,
    calculated_fields: Dict[str, Any]
) -> bool:
    """
    Actualiza un BodyMeasurement con los campos calculados.

    NOTA: Esta función debe ser llamada desde Django API, no desde Celery,
    ya que Celery worker no tiene acceso a los modelos de Django.

    Args:
        measurement_id: UUID de la medición
        calculated_fields: Dict con campos calculados por la tarea

    Returns:
        True si se actualizó correctamente

    Example:
        # En Django API, después de recibir resultado de Celery:
        >>> from vectosvc.worker.body_tasks import update_measurement_with_calculations
        >>> result = task.get()
        >>> if result['status'] == 'success':
        ...     update_measurement_with_calculations(
        ...         measurement_id,
        ...         result['calculated_fields']
        ...     )
    """
    try:
        # Importar Django model (solo funciona en Django context)
        from body.models import BodyMeasurement

        measurement = BodyMeasurement.objects.get(id=measurement_id)

        # Actualizar campos calculados
        for field, value in calculated_fields.items():
            if hasattr(measurement, field) and value is not None:
                setattr(measurement, field, value)

        measurement.save(update_fields=list(calculated_fields.keys()))

        logger.info(
            f"✅ Updated measurement {measurement_id} with {len(calculated_fields)} calculated fields"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Failed to update measurement {measurement_id}: {e}")
        return False
