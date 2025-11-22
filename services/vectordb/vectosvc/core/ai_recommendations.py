"""
Generación de Recomendaciones con IA

Módulo para generar recomendaciones personalizadas usando LLM (Gemini).

Integra múltiples fuentes de datos:
- Tendencias de progreso corporal
- Adherencia nutricional
- Mediciones antropométricas
- Objetivos del usuario
- Conocimiento médico y nutricional

Referencias:
- Personalized Nutrition Recommendations using ML
- AI in Healthcare: Best Practices
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from loguru import logger


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Obtener API key de Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
USE_GEMINI = bool(GEMINI_API_KEY)

# Configuración del modelo
DEFAULT_MODEL = "gemini-1.5-flash"  # Rápido y económico
TEMPERATURE = 0.7  # Balance entre creatividad y consistencia
MAX_OUTPUT_TOKENS = 2048


# ============================================================================
# CONSTANTES
# ============================================================================

class RecommendationType:
    """Tipos de recomendaciones."""
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    LIFESTYLE = "lifestyle"
    MEDICAL = "medical"
    MOTIVATIONAL = "motivational"


class Priority:
    """Niveles de prioridad."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

SYSTEM_PROMPT = """Eres un asistente experto en nutrición y salud que proporciona recomendaciones personalizadas basadas en datos objetivos.

IMPORTANTE:
- Tus recomendaciones deben ser específicas, accionables y basadas en evidencia científica
- Usa un tono profesional pero empático
- Prioriza la salud y seguridad del usuario
- Si detectas algo preocupante, recomienda consultar a un profesional
- No hagas diagnósticos médicos
- Sé conciso pero completo

FORMATO DE RESPUESTA:
Genera exactamente 5 recomendaciones en el siguiente formato JSON:

```json
{
  "recommendations": [
    {
      "type": "nutrition" | "exercise" | "lifestyle" | "medical" | "motivational",
      "priority": "high" | "medium" | "low",
      "title": "Título breve de la recomendación",
      "description": "Explicación detallada (2-3 oraciones)",
      "rationale": "Por qué es importante basado en los datos del usuario",
      "action_steps": ["Paso 1", "Paso 2", "Paso 3"]
    }
  ],
  "overall_assessment": "Evaluación general del progreso y estado actual (2-3 oraciones)",
  "key_focus_areas": ["Área 1", "Área 2", "Área 3"]
}
```

RESPONDE ÚNICAMENTE CON EL JSON, SIN TEXTO ADICIONAL."""


def _build_user_context_prompt(
    user_data: Dict[str, Any],
    trends: Optional[Dict[str, Any]],
    adherence: Optional[Dict[str, Any]],
    latest_measurement: Optional[Dict[str, Any]]
) -> str:
    """Construye el prompt contextual con datos del usuario."""
    sections = []

    # Sección 1: Datos demográficos y objetivos
    sections.append("## DATOS DEL USUARIO")
    if user_data.get('age'):
        sections.append(f"- Edad: {user_data['age']} años")
    if user_data.get('gender'):
        sections.append(f"- Género: {user_data['gender']}")
    if user_data.get('patient_type'):
        sections.append(f"- Tipo: {user_data['patient_type']}")
    if user_data.get('goal'):
        sections.append(f"- Objetivo: {user_data['goal']}")

    # Sección 2: Mediciones actuales
    if latest_measurement:
        sections.append("\n## MEDICIONES ACTUALES")
        if latest_measurement.get('weight_kg'):
            sections.append(f"- Peso: {latest_measurement['weight_kg']} kg")
        if latest_measurement.get('height_cm'):
            sections.append(f"- Estatura: {latest_measurement['height_cm']} cm")
        if latest_measurement.get('bmi'):
            sections.append(f"- IMC: {latest_measurement['bmi']}")
        if latest_measurement.get('body_fat_percentage'):
            sections.append(f"- Grasa corporal: {latest_measurement['body_fat_percentage']}%")
        if latest_measurement.get('muscle_mass_kg'):
            sections.append(f"- Masa muscular: {latest_measurement['muscle_mass_kg']} kg")
        if latest_measurement.get('cardiovascular_risk'):
            sections.append(f"- Riesgo cardiovascular: {latest_measurement['cardiovascular_risk']}")

    # Sección 3: Tendencias de progreso
    if trends and trends.get('trends'):
        sections.append("\n## TENDENCIAS DE PROGRESO")
        sections.append(f"- Período analizado: {trends.get('measurement_count', 0)} mediciones en {trends.get('period', {}).get('days', 0)} días")

        for metric, trend_data in trends['trends'].items():
            if metric == 'weight_kg':
                direction = trend_data.get('direction', 'stable')
                change = trend_data.get('change_total', 0)
                velocity = trend_data.get('velocity_per_week', 0)

                direction_es = {
                    'increasing': 'aumentando',
                    'decreasing': 'disminuyendo',
                    'stable': 'estable'
                }.get(direction, direction)

                sections.append(
                    f"- Peso: {direction_es} ({change:+.1f} kg total, {velocity:+.2f} kg/semana)"
                )

            elif metric == 'body_fat_percentage':
                change = trend_data.get('change_total', 0)
                sections.append(f"- Grasa corporal: {change:+.1f}%")

            elif metric == 'muscle_mass_kg':
                change = trend_data.get('change_total', 0)
                sections.append(f"- Masa muscular: {change:+.1f} kg")

        if trends.get('alerts'):
            sections.append(f"\n**Alertas detectadas**: {len(trends['alerts'])}")
            for alert in trends['alerts'][:3]:  # Máximo 3 alertas
                sections.append(f"  - {alert.get('message', '')}")

    # Sección 4: Adherencia nutricional
    if adherence and adherence.get('adherence_level') != 'insufficient_data':
        sections.append("\n## ADHERENCIA NUTRICIONAL")
        level = adherence.get('adherence_level', 'unknown')
        overall_rate = adherence.get('adherence_rates', {}).get('overall', 0)

        level_es = {
            'excellent': 'excelente',
            'good': 'buena',
            'moderate': 'moderada',
            'poor': 'pobre'
        }.get(level, level)

        sections.append(f"- Adherencia general: {level_es} ({overall_rate:.1f}%)")
        sections.append(f"- Cobertura de registros: {adherence.get('coverage', 0):.1f}%")

        rates = adherence.get('adherence_rates', {})
        sections.append(f"- Calorías: {rates.get('calories', 0):.1f}% del objetivo")
        sections.append(f"- Proteína: {rates.get('protein', 0):.1f}% del objetivo")

        if adherence.get('issues'):
            sections.append(f"\n**Problemas detectados**: {len(adherence['issues'])}")
            for issue in adherence['issues'][:3]:  # Máximo 3 problemas
                sections.append(f"  - {issue.get('description', '')}")

        trends_data = adherence.get('trends', {})
        if trends_data.get('improving') is not None:
            improving = "mejorando" if trends_data['improving'] else "sin mejora"
            sections.append(f"- Tendencia: {improving}")

    return "\n".join(sections)


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def generate_ai_recommendations(
    user_id: str,
    user_data: Dict[str, Any],
    trends: Optional[Dict[str, Any]] = None,
    adherence: Optional[Dict[str, Any]] = None,
    latest_measurement: Optional[Dict[str, Any]] = None,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Genera recomendaciones personalizadas usando IA.

    Args:
        user_id: UUID del usuario
        user_data: Datos demográficos y objetivos
            {
                'age': int,
                'gender': str,
                'patient_type': str,
                'goal': str
            }
        trends: Análisis de tendencias de progreso (output de analyze_measurement_trends)
        adherence: Análisis de adherencia nutricional (output de analyze_nutrition_adherence)
        latest_measurement: Última medición corporal
        model: Modelo de LLM a usar (default: gemini-1.5-flash)

    Returns:
        Dict con recomendaciones:
        {
            'user_id': str,
            'generated_at': str,
            'model': str,
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
            'key_focus_areas': List[str],
            'source_data': {
                'has_trends': bool,
                'has_adherence': bool,
                'has_measurement': bool
            }
        }
    """
    logger.info(f"🤖 Generating AI recommendations for user {user_id}")

    # Construir contexto
    user_context = _build_user_context_prompt(
        user_data, trends, adherence, latest_measurement
    )

    # Generar recomendaciones
    if USE_GEMINI:
        recommendations_data = _generate_with_gemini(user_context, model)
    else:
        logger.warning("Gemini API not configured, using fallback recommendations")
        recommendations_data = _generate_fallback_recommendations(
            user_data, trends, adherence
        )

    # Validar y estructurar respuesta
    result = {
        'user_id': user_id,
        'generated_at': _get_current_timestamp(),
        'model': model if USE_GEMINI else 'fallback',
        'recommendations': recommendations_data.get('recommendations', []),
        'overall_assessment': recommendations_data.get('overall_assessment', ''),
        'key_focus_areas': recommendations_data.get('key_focus_areas', []),
        'source_data': {
            'has_trends': trends is not None and bool(trends.get('trends')),
            'has_adherence': adherence is not None and adherence.get('adherence_level') != 'insufficient_data',
            'has_measurement': latest_measurement is not None
        }
    }

    logger.success(
        f"✅ Generated {len(result['recommendations'])} recommendations for user {user_id}"
    )

    return result


def _generate_with_gemini(user_context: str, model: str) -> Dict[str, Any]:
    """Genera recomendaciones usando la API de Gemini."""
    try:
        from google import genai
        from google.genai.types import GenerateContentConfig

        # Inicializar cliente
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Construir prompt completo
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_context}\n\nGenera las recomendaciones en formato JSON:"

        # Configuración
        config = GenerateContentConfig(
            temperature=TEMPERATURE,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )

        # Generar
        logger.debug(f"Calling Gemini API with model {model}")
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=config
        )

        # Extraer texto
        response_text = response.text

        # Intentar parsear JSON
        # A veces Gemini envuelve el JSON en markdown
        if '```json' in response_text:
            # Extraer JSON del bloque de código
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()

        # Parsear JSON
        recommendations = json.loads(response_text)

        logger.debug("Successfully parsed Gemini response")
        return recommendations

    except ImportError:
        logger.error("google-genai library not installed")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON response: {e}")
        logger.debug(f"Raw response: {response_text[:500]}")
        raise
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        raise


def _generate_fallback_recommendations(
    user_data: Dict[str, Any],
    trends: Optional[Dict[str, Any]],
    adherence: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Genera recomendaciones básicas sin IA cuando no hay API disponible."""
    recommendations = []

    # Recomendación 1: Basada en adherencia
    if adherence and adherence.get('adherence_level') == 'poor':
        recommendations.append({
            'type': RecommendationType.NUTRITION,
            'priority': Priority.HIGH,
            'title': 'Mejorar adherencia al plan nutricional',
            'description': 'Tu adherencia actual es baja. Es fundamental seguir el plan para alcanzar tus objetivos.',
            'rationale': f"Adherencia actual: {adherence.get('adherence_rates', {}).get('overall', 0):.1f}%",
            'action_steps': [
                'Planifica tus comidas con anticipación',
                'Prepara tus alimentos en batch',
                'Registra todo lo que comes'
            ]
        })

    # Recomendación 2: Basada en tendencias
    if trends and trends.get('alerts'):
        first_alert = trends['alerts'][0]
        recommendations.append({
            'type': RecommendationType.LIFESTYLE,
            'priority': Priority.HIGH,
            'title': 'Atender alerta detectada',
            'description': first_alert.get('message', ''),
            'rationale': 'Cambio significativo detectado en tus métricas',
            'action_steps': [first_alert.get('recommendation', 'Consulta con tu profesional')]
        })

    # Recomendaciones genéricas
    if len(recommendations) < 3:
        recommendations.extend([
            {
                'type': RecommendationType.EXERCISE,
                'priority': Priority.MEDIUM,
                'title': 'Mantener actividad física regular',
                'description': 'El ejercicio es fundamental para mantener masa muscular y salud cardiovascular.',
                'rationale': 'Recomendación general basada en evidencia científica',
                'action_steps': [
                    'Al menos 150 minutos de ejercicio moderado por semana',
                    'Incluir entrenamiento de fuerza 2-3 veces por semana'
                ]
            },
            {
                'type': RecommendationType.LIFESTYLE,
                'priority': Priority.MEDIUM,
                'title': 'Priorizar calidad de sueño',
                'description': 'El sueño adecuado es crucial para la recuperación y el control del peso.',
                'rationale': 'El sueño afecta hormonas del apetito y recuperación muscular',
                'action_steps': [
                    'Dormir 7-9 horas por noche',
                    'Mantener horarios regulares'
                ]
            }
        ])

    return {
        'recommendations': recommendations[:5],
        'overall_assessment': 'Continúa trabajando en tus objetivos de salud. Enfócate en mantener consistencia.',
        'key_focus_areas': ['Nutrición', 'Ejercicio', 'Descanso']
    }


def _get_current_timestamp() -> str:
    """Obtiene timestamp actual en formato ISO."""
    from datetime import datetime
    return datetime.now().isoformat()


# ============================================================================
# FUNCIONES DE FORMATEO
# ============================================================================

def format_recommendations_for_display(
    recommendations_data: Dict[str, Any]
) -> str:
    """Formatea las recomendaciones para mostrar en texto plano."""
    lines = []

    lines.append("=" * 60)
    lines.append("RECOMENDACIONES PERSONALIZADAS")
    lines.append("=" * 60)
    lines.append("")

    # Overall assessment
    if recommendations_data.get('overall_assessment'):
        lines.append("EVALUACIÓN GENERAL:")
        lines.append(recommendations_data['overall_assessment'])
        lines.append("")

    # Recomendaciones
    lines.append("RECOMENDACIONES:")
    lines.append("")

    for i, rec in enumerate(recommendations_data.get('recommendations', []), 1):
        priority_symbol = {
            Priority.HIGH: '🔴',
            Priority.MEDIUM: '🟡',
            Priority.LOW: '🟢'
        }.get(rec.get('priority', Priority.MEDIUM), '⚪')

        lines.append(f"{i}. {priority_symbol} {rec.get('title', 'Sin título')}")
        lines.append(f"   Tipo: {rec.get('type', 'general')}")
        lines.append(f"   {rec.get('description', '')}")
        lines.append(f"   Razón: {rec.get('rationale', '')}")

        if rec.get('action_steps'):
            lines.append("   Pasos a seguir:")
            for step in rec['action_steps']:
                lines.append(f"     - {step}")

        lines.append("")

    # Key focus areas
    if recommendations_data.get('key_focus_areas'):
        lines.append("ÁREAS CLAVE DE ENFOQUE:")
        for area in recommendations_data['key_focus_areas']:
            lines.append(f"  • {area}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)
